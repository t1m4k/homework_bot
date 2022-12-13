import logging
import os
import sys
import time
from logging.handlers import RotatingFileHandler

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PR_TOKEN')
TELEGRAM_TOKEN = os.getenv('TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(
    'my_logger.log', maxBytes=50000000, backupCount=5
)
logger.addHandler(handler)


class GetApiAnswerError(Exception):
    """Обработка ошибок."""

    def __init__(self, *args):
        """Конструктор класса."""
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        """Метод."""
        if self.message:
            return 'GetApiAnswerError, {0} '.format(self.message)
        return 'GetApiAnswerError has been raised'


class SendMessageError(Exception):
    """Обработка ошибок."""

    def __init__(self, *args):
        """Конструктор класса."""
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        """Метод."""
        if self.message:
            return 'SendMessageError, {0} '.format(self.message)
        return 'SendMessageError has been raised'


def check_tokens():
    """Функция проверки доступности переменных окружения."""
    if all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)):
        return True
    logging.critical('отсутствие обязательных переменных')
    return check_tokens()


def send_message(bot, message):
    """Функция отпраки сообщений."""
    logger.debug('Начало отправки сообщения')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        logger.error('Сообщение не отправлено')
        raise SendMessageError(error)
    else:
        logging.debug('Сообщение отправлено')


def get_api_answer(timestamp):
    """Функция запроса к эндпоинту."""
    try:
        params = {'from_date': timestamp}
        homework_statuses = requests.get(
            ENDPOINT, headers=HEADERS, params=params
        )
    except requests.RequestException as error:
        logger.error('requestexeption')
        raise GetApiAnswerError(error)
    else:
        if homework_statuses.status_code != 200:
            raise ConnectionError('Ошибка подключения')
        response = homework_statuses.json()
    return response


def check_response(response):
    """Функция проверки типа данных."""
    if not isinstance(response, dict):
        raise TypeError('Ответ не словарь')
    if not isinstance(response.get('homeworks'), list):
        raise TypeError('Ответ не список')
    if response.get('homeworks') is None:
        raise KeyError('Нет ключа homeworks')
    if not response.get('homeworks'):
        logger.debug('Статус работы не изменился')
    if len(response.get('homeworks')) == 0:
        return None
    return response.get('homeworks')[0]


def parse_status(homework):
    """Функция для извлечения статуса домашней работы."""
    if not homework:
        raise KeyError('Статус не определен')
    if homework.get('homework_name') is None:
        raise KeyError('homework_name не найден')
    homework_name = homework.get('homework_name')
    homework_verdict = homework.get('status')
    if homework_verdict not in HOMEWORK_VERDICTS:
        raise KeyError('Статус не определен')
    verdict = HOMEWORK_VERDICTS[homework_verdict]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    timestamp = 0
    old_message = ''

    if not check_tokens():
        sys.exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    send_message(bot, 'Start')
    while True:
        try:
            response = get_api_answer(timestamp)
            timestamp = response.get('current_date')
            homework = check_response(response)
            if homework is None:
                logger.debug('Нет обновления')
            else:
                message = parse_status(homework)
                if message != old_message:
                    send_message(bot, message)
                    message = old_message
                else:
                    if not send_message:
                        logger.debug('Ответ не изменился')
                    else:
                        raise ConnectionError('Ошибка подключения')

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            logger.error(error, exc_info=True)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    main()
