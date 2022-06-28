import os
import random
import logging
from enum import Enum

from telegram import Bot, Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (Updater, CommandHandler, MessageHandler, RegexHandler,
                          ConversationHandler, CallbackContext, Filters)

from dotenv import load_dotenv
import redis

from utils.telegram_logger import TelegramLogsHandler


logger = logging.getLogger('Telegram logger')

redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)


class Conversation(Enum):
    QUESTION = 1
    ANSWER = 2


def start(update: Update, context: CallbackContext):
    custom_keyboard = [['Новый вопрос', 'Сдаться'],
                       ['Мой счет']]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Здравствуйте. Нажмите "Новый вопрос" чтобы начать игру.',
        reply_markup=reply_markup
    )

    return Conversation.QUESTION


def handle_new_question_request(update: Update, context: CallbackContext):
    questions_and_answers = quiz()
    random_question_number = random.randint(1, len(questions_and_answers)-1)
    question = quiz()[random_question_number][0]

    redis_client.set(update.effective_chat.id, question)

    context.bot.send_message(chat_id=update.effective_chat.id, text=question)

    return Conversation.ANSWER


def handle_solution_attempt(update: Update, context: CallbackContext):
    question = redis_client.get(update.effective_chat.id)
    answer_raw = find_answer(question).split('Ответ:\n')[-1]
    answer = answer_raw[:-1].lower()

    if update.message.text.lower() == answer:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»'
        )
        return Conversation.QUESTION

    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f'Неправильно… Правильный ответ: {answer_raw} Попробуешь ещё раз?')


def cancel(update: Update, context: CallbackContext):
    update.message.reply_text('Игра прекращена. Введите "/start" чтобы начать игру заного.',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def error_handler(update: object, context: CallbackContext) -> None:
    logger.error(msg="Exception while handling telegram update:", exc_info=context.error)


def quiz():
    with open("quiz_questions/3f15.txt", "r", encoding="KOI8-R") as my_file:
      file_contents = my_file.read()
      questions_and_answers = file_contents.split('\n\n')

    questions = []
    answers = []
    for sentence in questions_and_answers:
        if sentence.startswith('Вопрос'):
            questions.append(sentence)
        elif sentence.startswith('Ответ'):
            answers.append(sentence)

    merged_questions_and_answers = list(zip(questions, answers))

    return merged_questions_and_answers


def find_answer(question):
    question_and_answer = list(
        filter(
            lambda question_and_answer: question_and_answer[0] == question,
            quiz()
        )
    )[0]
    answer = question_and_answer[1]

    return answer


def main():
    load_dotenv()

    telegram_logger_bot_token = os.getenv('TELEGRAM_LOGGER_BOT_TOKEN')
    developer_chat_id = os.getenv('TELEGRAM_DEVELOPER_USER_ID')

    logger_tg_bot = Bot(token=telegram_logger_bot_token)

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logger.setLevel(logging.INFO)
    logger.addHandler(TelegramLogsHandler(logger_tg_bot, developer_chat_id))

    updater = Updater(token=os.getenv('TELEGRAM_BOT_TOKEN'))
    dispatcher = updater.dispatcher

    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            Conversation.QUESTION: [RegexHandler('^Новый вопрос$', handle_new_question_request)],
            Conversation.ANSWER: [MessageHandler(Filters.text, handle_solution_attempt)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(conversation_handler)

    dispatcher.add_error_handler(error_handler)

    updater.start_polling()


if __name__ == '__main__':
    main()
