import os
import json
import logging
import requests

# Токен вашего Telegram-бота
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_API_URL = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/'

# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_message(chat_id, text):
    """
    Отправляет сообщение в Telegram чат.
    """
    url = TELEGRAM_API_URL + 'sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': text
    }
    response = requests.post(url, json=payload)
    return response.json()

def handle_update(update):
    """
    Обрабатывает входящее обновление от Telegram.
    """
    try:
        message = update.get('message', {})
        chat_id = message.get('chat', {}).get('id')
        text = message.get('text', '')

        if text == '/start':
            send_message(chat_id, 'Привет! Я ваш Telegram-бот.')
        else:
            send_message(chat_id, f'Вы сказали: {text}')
    except Exception as e:
        logger.error(f'Ошибка при обработке обновления: {e}')

def handler(event, context):
    """
    Основной обработчик для Yandex Cloud Function.
    """
    try:
        # Получаем тело запроса
        body = json.loads(event['body'])
        logger.info(f'Received update: {body}')

        # Обрабатываем обновление
        handle_update(body)

        # Возвращаем успешный ответ
        return {
            'statusCode': 200,
            'body': 'OK'
        }
    except Exception as e:
        logger.error(f'Ошибка в handler: {e}')
        return {
            'statusCode': 500,
            'body': 'Internal Server Error'
        }