import os
import json
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

# Координаты Витебска (дефолт)
LAT = 55.19
LON = 30.20

# Хранилище локаций юзеров {chat_id: {"lat": float, "lon": float, "name": str}}
user_locations = {}
LOCATIONS_FILE = os.path.join(os.path.dirname(__file__), "locations.json")

def load_locations():
    """Загружает локации из файла"""
    global user_locations
    if os.path.exists(LOCATIONS_FILE):
        try:
            with open(LOCATIONS_FILE, "r", encoding="utf-8") as f:
                user_locations = json.load(f)
        except:
            user_locations = {}

def save_locations():
    """Сохраняет локации в файл"""
    with open(LOCATIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(user_locations, f, ensure_ascii=False, indent=2)

# Загружаем при старте
load_locations()

def get_pollen_data(lat=LAT, lon=LON):
    url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&hourly=birch_pollen,alder_pollen&timezone=Europe/Minsk"
    response = requests.get(url).json()

    # Берём текущее время в нужной timezone
    from datetime import datetime, timezone, timedelta
    minsk_tz = timezone(timedelta(hours=3))
    current_time_minsk = datetime.now(minsk_tz)
    current_hour = current_time_minsk.hour

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

def get_pollen_message(location_name="Витебск", lat=LAT, lon=LON):
    pollen = get_pollen_data(lat, lon)

    message = f"🌲 Пыльца в {location_name}:\n\n"
    message += get_status(pollen["birch"], "Берёза") + "\n"
    message += get_status(pollen["alder"], "Ольха")

    return message

def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    if reply_markup:
        data["reply_markup"] = reply_markup
    requests.post(url, json=data)

def get_location_keyboard():
    """Возвращает клавиатуру с кнопкой запроса локации"""
    return json.dumps({
        "keyboard": [[{"text": "📍 Отправить локацию", "request_location": True}]],
        "resize_keyboard": True
    }, ensure_ascii=False)

def remove_keyboard_markup():
    """Убирает клавиатуру"""
    return json.dumps({"remove_keyboard": True}, ensure_ascii=False)

def is_pollen_season():
    """Проверяет, идёт ли сезон цветения (15 февраля - 15 июня)"""
    from datetime import datetime
    minsk_tz = timezone(timedelta(hours=3))
    now = datetime.now(minsk_tz)
    # Сезон: 15 февраля (день 46) - 15 июня (день 166)
    day_of_year = now.timetuple().tm_yday
    return 46 <= day_of_year <= 166

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

            # Обработка локации
            if "location" in message:
                loc = message["location"]
                user_locations[chat_id] = {"lat": loc["latitude"], "lon": loc["longitude"], "name": "вашем месте"}
                save_locations()
                send_message(chat_id, "📍 Локация сохранена!", reply_markup=remove_keyboard_markup())
                updates_to_delete.append(result["update_id"])
                continue

            if text == "/check":
                # Используем сохранённую локацию или дефолт
                if chat_id in user_locations:
                    loc = user_locations[chat_id]
                    msg = get_pollen_message(loc["name"], loc["lat"], loc["lon"])
                else:
                    msg = get_pollen_message()
                send_message(chat_id, msg)

            if text in ["/start", "/check"]:
                if text == "/start":
                    send_message(
                        chat_id,
                        "🌲 Привет! Я помогу следить за уровнем пыльцы.\n\n"
                        "Команды:\n/check - узнать уровень пыльцы\n\n"
                        "Нажми кнопку ниже, чтобы получать данные для твоего местоположения:",
                        reply_markup=get_location_keyboard()
                    )

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

                        # Обработка локации
                        if "location" in message:
                            loc = message["location"]
                            user_locations[chat_id] = {"lat": loc["latitude"], "lon": loc["longitude"], "name": "вашем месте"}
                            save_locations()
                            send_message(chat_id, "📍 Локация сохранена! Теперь /check показывает данные для вашей местности.")
                            continue

                        if text == "/check":
                            # Используем сохранённую локацию или дефолт
                            if chat_id in user_locations:
                                loc = user_locations[chat_id]
                                msg = get_pollen_message(loc["name"], loc["lat"], loc["lon"])
                            else:
                                msg = get_pollen_message()
                            send_message(chat_id, msg)

                        if text in ["/start"]:
                            send_message(
                                chat_id,
                                "🌲 Привет! Я помогу следить за уровнем пыльцы.\n\n"
                                "Команды:\n/check - узнать уровень пыльцы\n\n"
                                "Нажми кнопку ниже, чтобы получать данные для твоего местоположения:",
                                reply_markup=get_location_keyboard()
                            )
            except Exception as e:
                print(f"Ошибка: {e}")
                time.sleep(5)

    else:
        # Режим по расписанию - проверяет сезон
        if not is_pollen_season():
            print("Вне сезона цветения, пропуск")
            return

        # Проверяет команды и отправляет уведомление
        check_and_reply_commands()

        if TELEGRAM_CHAT_ID:
            send_message(TELEGRAM_CHAT_ID, get_pollen_message())

if __name__ == "__main__":
    main()
