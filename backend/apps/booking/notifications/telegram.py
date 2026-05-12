import requests
from django.conf import settings


def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": chat_id,
        "text": text,
    }

    try:
        response = requests.post(url, json=data)

        if response.status_code != 200:
            print("Ошибка Telegram:", response.text)

    except Exception as e:
        print("Ошибка отправки сообщения:", e)