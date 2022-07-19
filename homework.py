import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

# from pprint import pprint

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    filename='main.log',
    filemode='a',
    format='%(asctime)s, %(levelname)s, %(message)s'
)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 20  # 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Check TOKENs exist."""
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        return True
    return False


def get_api_answer(current_timestamp):
    """Get api from server."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != 200:
        logging.error('Эндпойнт недоступен. response.status_code:'
                      + f'{response.status_code}')
        raise Exception
    return response.json()


def check_response(response):
    """Parse response and check expected type."""
    homeworks = response['homeworks']
    if type(homeworks) != list:
        logging.error('Тип данных ответа невалидный.')
        raise Exception
    return homeworks


def parse_status(homework):
    """Parse status and message text return."""
    # подгонял под тесты, ваще хотел всё под try: сунуть.
    try:
        homework_name = homework['homework_name']
    except Exception as error:
        logging.error(f'Отсутствие ожидаемых ключей в ответе API: {error}')
    homework_status = homework['status']
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def send_message(bot, message):
    """Send a message and log it."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info(
            f'Удачная отправка сообщения: {message}')
    except Exception as error:
        logging.error(f'Cбой при отправке сообщения: {error}')


def main():
    """The main logic of bot."""
    if not check_tokens():
        logging.critical('Отсутствуют обязательные переменные окружения!')
        raise SystemExit
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    # current_timestamp = 1655577239  # минус месяц для дебага
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if homeworks:
                message = parse_status(homeworks[0])
                send_message(bot, message)
                current_timestamp = response['current_date']
            time.sleep(RETRY_TIME)
        except Exception as error:
            print(error)
            logging.error(f'Сбой в работе программы: {error}')
            message = f'Сбой в работе программы: {error}'
            bot.send_message(TELEGRAM_CHAT_ID, message)
            time.sleep(RETRY_TIME)
        else:
            ...  # зачем здесь это я пока не знаю


if __name__ == '__main__':
    main()
