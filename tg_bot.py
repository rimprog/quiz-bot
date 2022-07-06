import os
import random
import logging
from enum import Enum

from telegram import Bot, Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (Updater, CommandHandler, MessageHandler, RegexHandler,
                          ConversationHandler, CallbackContext, Filters)

from dotenv import load_dotenv
import redis

from utils.quiz import get_quiz
from utils.telegram_logger import TelegramLogsHandler


logger = logging.getLogger('Telegram logger')


class Conversation(Enum):
    QUESTION = 1
    ANSWER = 2


def start(update: Update, context: CallbackContext):
    redis_url = os.getenv('REDIS_URL')
    redis_client = redis.from_url(redis_url, db=0, decode_responses=True)

    context.bot_data['redis_client'] = redis_client
    context.bot_data['quiz'] = get_quiz()

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
    questions_and_answers = context.bot_data['quiz']
    question = random.choice(list(questions_and_answers.items()))[0]

    redis_client = context.bot_data['redis_client']
    redis_client.set(update.effective_chat.id, question)

    context.bot.send_message(chat_id=update.effective_chat.id, text=question)

    return Conversation.ANSWER


def handle_solution_attempt(update: Update, context: CallbackContext):
    redis_client = context.bot_data['redis_client']
    question = redis_client.get(update.effective_chat.id)
    questions_and_answers = context.bot_data['quiz']

    answer_raw = questions_and_answers[question].split('Ответ:\n')[-1]
    answer = answer_raw[:-1].lower()

    if update.message.text.lower() == answer:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»'
        )

        return Conversation.QUESTION


def handle_surrender_request(update: Update, context: CallbackContext):
    redis_client = context.bot_data['redis_client']

    questions_and_answers = context.bot_data['quiz']
    question = redis_client.get(update.effective_chat.id)
    answer = questions_and_answers[question].split('Ответ:\n')[-1]

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'Правильный ответ: {answer}'
    )

    handle_new_question_request(update, context)


def cancel(update: Update, context: CallbackContext):
    update.message.reply_text('Игра прекращена. Введите "/start" чтобы начать игру заного.',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def error_handler(update: object, context: CallbackContext) -> None:
    logger.error(msg="Exception while handling telegram update:", exc_info=context.error)


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
            Conversation.ANSWER: [RegexHandler('^Сдаться$', handle_surrender_request),
                                  MessageHandler(Filters.text, handle_solution_attempt)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(conversation_handler)

    dispatcher.add_error_handler(error_handler)

    updater.start_polling()


if __name__ == '__main__':
    main()
