import json
import logging
import os
import sys
import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from telebot import TeleBot

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверяет доступность необходимых переменных окружения."""
    tokens = (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
    for token in tokens:
        if not token:
            logger.critical('Не найдена переменная окружения.')
            raise ValueError('Не найдена переменная окружения.')


def send_message(bot, message):
    """Отправляет сообщение в Telegram-чат."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.debug(f'Сообщение "{message}" отправлено.')
    except Exception as error:
        logger.error(f'Ошибка {error}, сообщение не отправлено.')


def get_api_answer(timestamp):
    """Делает запрос к эндпоинту API-сервиса."""
    try:
        response = requests.get(
            ENDPOINT, headers=HEADERS, params={'from_date': timestamp}
        )
    except requests.RequestException:
        message = f'Ошибка {response.status_code} при запросе к API.'
        raise requests.RequestException(message)
    if response.status_code != HTTPStatus.OK:
        message = f'Ошибка {response.status_code}'
        raise requests.exceptions.HTTPError(message)
    try:
        return response.json()
    except json.decoder.JSONDecodeError:
        message = 'Невозможно преобразовать в JSON.'
        raise json.decoder.JSONDecodeError(message)


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    if not isinstance(response, dict):
        message = 'Структура данных не соответствует ожидаемому словарю.'
        raise TypeError(message)
    if 'homeworks' not in response:
        message = 'Отсутствует ключ "homeworks" в ответе API.'
        raise KeyError(message)
    if not isinstance(response["homeworks"], list):
        message = 'Под ключом "homeworks" данные приходят не в виде списка.'
        raise TypeError(message)
    homeworks = response['homeworks']
    if not homeworks:
        return dict(homeworks)
    return homeworks[0]


def parse_status(homework):
    """Извлекает статус домашней работы работы."""
    homework_name = homework.get('homework_name')
    if not homework_name:
        message = 'Отсутствует ключ "homework_name в ответе API.'
        raise KeyError(message)
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_VERDICTS:
        message = 'Статус домашней работы не соответствует ожидаемому.'
        raise ValueError(message)
    verdict = HOMEWORK_VERDICTS.get(homework_status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time()) - RETRY_PERIOD
    no_error = True

    while True:
        try:
            api_answer = get_api_answer(timestamp)
            homework = check_response(api_answer)
            if homework:
                homework_status = parse_status(homework)
                send_message(bot, homework_status)
            else:
                logger.debug('Новые статусы отсутствуют.')
            timestamp = api_answer.get('current_date')
            no_error = True
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if no_error:
                send_message(bot, message)
                no_error = False
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
