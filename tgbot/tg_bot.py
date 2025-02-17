import os
import json
import logging
import requests
import boto3

# Токен вашего Telegram-бота
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
GPT_API_KEY = os.getenv('GPT_API_KEY')
TELEGRAM_API_URL = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/'
GPT_API_URI = os.getenv("GPT_API_URI")
GPT_API_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
BUCKET_NAME = os.getenv("BUCKET_NAME")
INSTRUCTION_KEY = os.getenv("INSTRUCTION_KEY")
STORAGE_ACCESS_KEY = os.getenv("STORAGE_ACCESS_KEY")
STORAGE_SECRET_KEY = os.getenv("STORAGE_SECRET_KEY")

# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_instruction():
    session = boto3.session.Session()
    s3 = session.client(
        service_name='s3',
        endpoint_url="https://storage.yandexcloud.net",
        aws_access_key_id=STORAGE_ACCESS_KEY,
        aws_secret_access_key=STORAGE_SECRET_KEY
    )

    obj = s3.get_object(Bucket=BUCKET_NAME, Key=INSTRUCTION_KEY)
    return obj['Body'].read().decode('utf-8')

instruction = get_instruction()

def ask_gpt(question):
    data = json.loads(instruction)

    headers = {'Content-Type': 'application/json',
               "Authorization": f"Api-Key {GPT_API_KEY}"}

    data["modelUri"] = GPT_API_URI
    data["messages"].append({
        "role": "user",
        "text": question
    })

    error_message = "Я не смог подготовить ответ на экзаменационный вопрос."
    try:
        response = requests.post(GPT_API_URL, headers=headers, json=data)

        if response.status_code == 200:
            return response.json()["result"]["alternatives"][0]["message"]["text"]
        else:
            return error_message
    except Exception as e:
        return error_message

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

        if "text" in message:
            question = message["text"]
        # elif "photo" in message:
        #     file_id = message["photo"][-1]["file_id"]
        #     question = get_text_from_photo(file_id)
        else:
            question = None

        if question == '/start':
            send_message(chat_id, 'Привет! Я ваш Telegram-бот.')
        elif question is None:
            send_message(chat_id, "Я могу обработать только текстовое сообщение или фотографию.")
        else:
            send_message(chat_id, ask_gpt(question))
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