import os
import requests
from datetime import datetime
import sys

# Читаем .env напрямую
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Координаты Витебска
LAT = 55.19
LON = 30.20

def get_pollen_data():
    url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={LAT}&longitude={LON}&hourly=birch_pollen,alder_pollen&timezone=Europe/Minsk"
    response = requests.get(url).json()

    # Получаем текущий час из API (уже в правильной timezone)
    current_time = response['hourly']['time'][-1]
    current_hour_str = current_time.split('T')[1][:2]  # "HH" из "2025-04-25T10:00"
    current_hour = int(current_hour_str)

    hourly = response['hourly']

    birch = hourly['birch_pollen'][current_hour]
    alder = hourly['alder_pollen'][current_hour]

    return {"birch": birch, "alder": alder}

def get_status(level, name):
    if level > 100:
        return f"🔴 {name}: {level} — ОПАСНО!"
    elif level > 10:
        return f"⚠️ {name}: {level} — Средний уровень"
    else:
        return f"✅ {name}: {level} — Низкий уровень"

def get_pollen_message():
    pollen = get_pollen_data()

    message = f"🌲 Пыльца в Витебске:\n\n"
    message += get_status(pollen["birch"], "Берёза") + "\n"
    message += get_status(pollen["alder"], "Ольха")

    return message

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    requests.post(url, json=data)

def check_and_reply_commands():
    """Проверяет и отвечает на команды /check"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?timeout=10"
    response = requests.get(url).json()

    updates_to_delete = []

    for result in response.get("result", []):
        if "message" in result:
            message = result["message"]
            chat_id = message["chat"]["id"]
            text = message.get("text", "")

            if text == "/check":
                send_message(chat_id, get_pollen_message())

            if text in ["/start", "/check"]:
                send_message(chat_id, "🌲 Бот пыльцы!\nКоманды:\n/check - узнать уровень пыльцы")

            updates_to_delete.append(result["update_id"])

    # Отмечаем обновления как обработанные
    if updates_to_delete:
        max_id = max(updates_to_delete)
        requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={max_id + 1}")

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "schedule"

    if mode == "poll":
        # Режим polling - работает постоянно, отвечает на команды
        print("Запуск в режиме polling...")
        import time
        offset = 0
        while True:
            try:
                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={offset}&timeout=30"
                response = requests.get(url).json()

                for result in response.get("result", []):
                    offset = result["update_id"] + 1

                    if "message" in result:
                        message = result["message"]
                        chat_id = message["chat"]["id"]
                        text = message.get("text", "")

                        if text == "/check":
                            send_message(chat_id, get_pollen_message())

                        if text in ["/start"]:
                            send_message(chat_id, "🌲 Бот пыльцы!\nКоманды:\n/check - узнать уровень пыльцы")
            except Exception as e:
                print(f"Ошибка: {e}")
                time.sleep(5)

    else:
        # Режим по расписанию - проверяет команды и отправляет уведомление
        check_and_reply_commands()

        if TELEGRAM_CHAT_ID:
            send_message(TELEGRAM_CHAT_ID, get_pollen_message())

if __name__ == "__main__":
    main()
