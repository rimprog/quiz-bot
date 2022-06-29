import os
import random
import logging

from vk_api import VkApi
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from telegram import Bot

import redis
from dotenv import load_dotenv

from utils.quiz import get_random_question, get_answer
from utils.telegram_logger import TelegramLogsHandler


load_dotenv()

logger = logging.getLogger('Telegram logger')

redis_url = os.getenv('REDIS_URL')
redis_client = redis.from_url(redis_url, db=0, decode_responses=True)


def create_keyboard():
    keyboard = VkKeyboard(one_time=True)

    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('Мой счет', color=VkKeyboardColor.PRIMARY)

    keyboard = keyboard.get_keyboard()

    return keyboard


def handle_start_request(event, vk_api, keyboard):
    vk_api.messages.send(
        user_id=event.user_id,
        keyboard=keyboard,
        message='Здравствуйте. Нажмите "Новый вопрос" чтобы начать игру.',
        random_id=random.randint(1,1000)
    )


def handle_new_question_request(event, vk_api, keyboard):
    question = get_random_question()

    redis_client.set(event.user_id, question)

    vk_api.messages.send(
        user_id=event.user_id,
        keyboard=keyboard,
        message=question,
        random_id=random.randint(1,1000)
    )


def handle_solution_attempt(event, vk_api, keyboard):
    question = redis_client.get(event.user_id)
    answer_raw = get_answer(question).split('Ответ:\n')[-1]
    answer = answer_raw[:-1].lower()

    if event.text.lower() == answer:
        vk_api.messages.send(
            user_id=event.user_id,
            keyboard=keyboard,
            message='Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»',
            random_id=random.randint(1,1000)
        )
    else:
        vk_api.messages.send(
            user_id=event.user_id,
            keyboard=keyboard,
            message='Неправильный ответ.',
            random_id=random.randint(1,1000)
        )


def handle_surrender_request(event, vk_api, keyboard):
    question = redis_client.get(event.user_id)
    answer = get_answer(question).split('Ответ:\n')[-1]

    vk_api.messages.send(
        user_id=event.user_id,
        keyboard=keyboard,
        message=f'Правильный ответ: {answer}',
        random_id=random.randint(1,1000)
    )


def handle_my_score_request(event, vk_api, keyboard):
    vk_api.messages.send(
        user_id=event.user_id,
        keyboard=keyboard,
        message='Опция временно недоступна.',
        random_id=random.randint(1,1000)
    )


def handle_conversation(event, vk_api):
    keyboard = create_keyboard()

    if event.text == "Начать":
        handle_start_request(event, vk_api, keyboard)

    elif event.text == "Новый вопрос":
        handle_new_question_request(event, vk_api, keyboard)

    elif event.text == "Сдаться":
        handle_surrender_request(event, vk_api, keyboard)
        handle_new_question_request(event, vk_api, keyboard)

    elif event.text == "Мой счет":
        handle_my_score_request(event, vk_api, keyboard)

    else:
        handle_solution_attempt(event, vk_api, keyboard)


def main():
    telegram_logger_bot_token = os.getenv('TELEGRAM_LOGGER_BOT_TOKEN')
    developer_chat_id = os.getenv('TELEGRAM_DEVELOPER_USER_ID')

    logger_tg_bot = Bot(token=telegram_logger_bot_token)

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logger.setLevel(logging.INFO)
    logger.addHandler(TelegramLogsHandler(logger_tg_bot, developer_chat_id))

    vk_session = VkApi(token=os.getenv('VK_TOKEN'))
    vk_api = vk_session.get_api()

    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            try:
                handle_conversation(event, vk_api)
            except Exception:
                logger.exception('An exception was raised while handling vkontakte event:')


if __name__ == '__main__':
    main()
