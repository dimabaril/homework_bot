import logging
import os
import sys
import time

import requests
import telegram
from dotenv import load_dotenv

import exceptions

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

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Check TOKENs exist."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def get_api_answer(current_timestamp):
    """Get api from server."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != 200:
        raise requests.HTTPError(
            'Эндпойнт недоступен.'
            f' response.status_code: {response.status_code}')
    return response.json()


def check_response(response):
    """Parse response and check expected type."""
    if not isinstance(response, dict):
        raise TypeError('Response type in not dict.'
                        f' response: {response}')
    if 'homeworks' not in response or 'current_date' not in response:
        raise KeyError('There are no necessary keys in the response.'
                       f' response: {response}')
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError('Homeworks type in not list.'
                        f' homeworks: {homeworks}')
    return homeworks


def parse_status(homework):
    """Parse status and message text return."""
    if 'homework_name' not in homework or 'status' not in homework:
        raise KeyError('There are no necessary keys in the homework.'
                       f' homework: {homework}')
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_STATUSES:
        raise KeyError('There are no necessary keys in the HOMEWORK_STATUSES.'
                       f' homework_status: {homework_status}')
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def send_message(bot, message):
    """Send a message and log it."""
    logging.info(f'Попытка отправки сообщения: {message}')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except:
        raise exceptions.SendMessageError
    else:
        logging.info(f'Удачная отправка сообщения: {message}')


def main():
    """The main logic of bot."""
    if not check_tokens():
        logging.critical('Отсутствуют обязательные переменные окружения!')
        # raise SystemExit # но выброс такой ошибки тоже закрывает программу
        # и нам не надо импортировать import sys
        sys.exit('Отсутствуют обязательные переменные окружения!')
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
        except Exception as error:
            logging.error(f'Сбой в работе программы: {error}')
            message = f'Сбой в работе программы: {error}'
            bot.send_message(TELEGRAM_CHAT_ID, message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
