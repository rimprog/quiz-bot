import os
import random
import logging

from telegram import Bot, Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext, Filters
from dotenv import load_dotenv
import redis

from utils.telegram_logger import TelegramLogsHandler


logger = logging.getLogger('Telegram logger')
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)


def error_handler(update: object, context: CallbackContext) -> None:
    logger.error(msg="Exception while handling telegram update:", exc_info=context.error)


def start(update: Update, context: CallbackContext):
    custom_keyboard = [['Новый вопрос', 'Сдаться'],
                       ['Мой счет']]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Здравствуйте',
        reply_markup=reply_markup
    )


def handle_new_question_request(update: Update, context: CallbackContext):
    if update.message.text == 'Новый вопрос':
        questions_and_answers = quiz()
        random_question_number = random.randint(1, len(questions_and_answers)-1)
        question = quiz()[random_question_number][0]

        redis_client.set(update.effective_chat.id, question)

        context.bot.send_message(chat_id=update.effective_chat.id, text=question)

    else:
        question = redis_client.get(update.effective_chat.id)
        answer = find_answer(question).split('Ответ:\n')[-1]

        if update.message.text == answer:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text='Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»'
            )
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text=f'Неправильно… Правильный ответ: {answer} Попробуешь ещё раз?')


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

    start_handler = CommandHandler('start', start)
    new_question_request_handler = MessageHandler(Filters.text & (~Filters.command), handle_new_question_request)

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(new_question_request_handler)

    dispatcher.add_error_handler(error_handler)

    updater.start_polling()


if __name__ == '__main__':
    main()
