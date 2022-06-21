import os
import logging

from telegram import Bot, Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext, Filters
from dotenv import load_dotenv

from utils.telegram_logger import TelegramLogsHandler


logger = logging.getLogger('Telegram logger')


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


def echo(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)


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
    print(merged_questions_and_answers)


def main():
    load_dotenv()
    quiz()

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
    echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(echo_handler)

    dispatcher.add_error_handler(error_handler)

    updater.start_polling()


if __name__ == '__main__':
    main()
