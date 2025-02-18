import base64
import os
import json
import logging

import requests
import boto3

CATALOG_ID = os.environ['CATALOG_ID']
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
GPT_API_KEY = os.getenv('GPT_API_KEY')
TELEGRAM_API_URL = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/'
GPT_API_URI = os.getenv("GPT_API_URI")
GPT_API_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
BUCKET_NAME = os.getenv("BUCKET_NAME")
INSTRUCTION_KEY = os.getenv("INSTRUCTION_KEY")
STORAGE_ACCESS_KEY = os.getenv("STORAGE_ACCESS_KEY")
STORAGE_SECRET_KEY = os.getenv("STORAGE_SECRET_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def encode_file(file_content):
    return base64.b64encode(file_content).decode("utf-8")


def get_file_path(file_id):
    url = TELEGRAM_API_URL + f'getFile?file_id={file_id}'
    response = requests.get(url).json()

    if "result" in response:
        return f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{response['result']['file_path']}"

    return None


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
    url = TELEGRAM_API_URL + 'sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': text
    }
    response = requests.post(url, json=payload)
    return response.json()


def extract_text_from_ocr(response_json):
    full_text = []
    try:
        result = response_json.get("result", {})
        logger.error(result)
        if not result:
            return ""

        text_annotation = result.get("textAnnotation", {})
        logger.error(text_annotation)

        blocks = text_annotation.get("blocks", [])
        logger.error(blocks)

        if not blocks:
            return ""

        for block in blocks:
            lines = block.get("lines", [])
            if not lines:
                continue

            for line in lines:
                text = line.get("text", "")
                if text:
                    full_text.append(text)

        # Собираем все строки в одну
        return "\n".join(full_text) if full_text else "Текст не найден на изображении."

    except Exception as e:
        return f"Ошибка обработки OCR-ответа: {e}"


def get_file_by_path(file_path):
    return requests.get(file_path)


def get_text_from_photo(response):
    content = encode_file(response.content)
    data = {"mimeType": "JPEG",
            "languageCodes": ["ru", "en"],
            "content": content}

    url = "https://ocr.api.cloud.yandex.net/ocr/v1/recognizeText"

    headers = {"Content-Type": "application/json",
               "Authorization": f"Api-Key {GPT_API_KEY}",
               "x-folder-id": f"{CATALOG_ID}",
               "x-data-logging-enabled": "true"}

    w = requests.post(url=url, headers=headers, data=json.dumps(data))
    if w.status_code == 200:
        return extract_text_from_ocr(w.json())
    else:
        return ""


def handle_update(update):
    try:
        message = update.get('message', {})
        chat_id = message.get('chat', {}).get('id')

        if "text" in message:
            question = message["text"]
        elif "photo" in message:
            if len(message["photo"]) > 4:  # С учетом разных размеров
                send_message(chat_id, "Я могу обработать только одну фотографию.")
                return
            file_id = message["photo"][-1]["file_id"]
            file_path = get_file_path(file_id)
            file_rs = get_file_by_path(file_path)
            question = get_text_from_photo(file_rs)
            logger.error(question)
        else:
            send_message(chat_id, "Я могу обработать только текстовое сообщение или фотографию.")
            return

        if question == '/start':
            send_message(chat_id, 'Привет! Я ваш Telegram-бот.')
        if question == '/help':
            send_message(chat_id, 'Напиши вопрос')
        elif question is None:
            send_message(chat_id, "Я могу обработать только текстовое сообщение или фотографию.")
        else:
            send_message(chat_id, ask_gpt(question))
    except Exception as e:
        logger.error(f'Ошибка при обработке обновления: {e}')


def handler(event, context):
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