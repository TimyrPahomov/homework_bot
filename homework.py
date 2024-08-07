import logging
import os
import requests
import sys
import time

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
    if not PRACTICUM_TOKEN:
        logger.critical('Не найдена переменная окружения "PRACTICUM_TOKEN".')
        raise ValueError('Не найдена переменная окружения "PRACTICUM_TOKEN".')
    if not TELEGRAM_TOKEN:
        logger.critical('Не найдена переменная окружения "TELEGRAM_TOKEN".')
        raise ValueError('Не найдена переменная окружения "TELEGRAM_TOKEN".')
    if not TELEGRAM_CHAT_ID:
        logger.critical('Не найдена переменная окружения "TELEGRAM_CHAT_ID".')
        raise ValueError('Не найдена переменная окружения "TELEGRAM_CHAT_ID".')


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
        if response.status_code != 200:
            raise requests.RequestException
    except requests.RequestException:
        logger.error(f'Ошибка {response.status_code} при запросе к API.')
        raise requests.RequestException
    except Exception as error:
        logger.error(f'Ошибка при запросе к API: {error}')
        raise Exception
    return response.json()


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    if not isinstance(response, dict):
        logger.error('Структура данных не соответствует ожидаемому словарю.')
        raise TypeError
    if 'homeworks' not in response:
        logger.error('Отсутствует ключ "homeworks" в ответе API.')
        raise KeyError('Не найден ключ "homeworks"')
    if not isinstance(response["homeworks"], list):
        logger.error(
            'Под ключом "homeworks" данные приходят не в виде списка'
        )
        raise TypeError
    homeworks = response['homeworks']
    if not homeworks:
        return homeworks
    else:
        return homeworks[0]


def parse_status(homework):
    """Извлекает статус домашней работы работы."""
    homework_name = homework.get('homework_name')
    if not homework_name:
        logger.error('Отсутствует ключ "homework_name в ответе API.')
        raise KeyError('Не найден ключ "homework_name"')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_VERDICTS:
        logger.error('Статус домашней работы не соответствует ожидаемому.')
        raise ValueError('Статус домашней работы не соответствует ожидаемому.')
    for status, text in HOMEWORK_VERDICTS.items():
        if status == homework_status:
            verdict = text
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    error_type = None

    while True:
        try:
            api_answer = get_api_answer(timestamp)
            homework = check_response(api_answer)
            if homework:
                homework_status = parse_status(homework)
                send_message(bot, homework_status)
            else:
                logger.debug('Новые статусы отсутствуют.')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if Exception != error_type:
                send_message(bot, message)
                error_type = Exception
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
