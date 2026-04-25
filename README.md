# 🌲 Pollen Bot

Telegram бот для отслеживания уровня пыльцы (берёза, ольха) в Витебске.

## Возможности

- 📊 Отчёт об уровне пыльцы (берёза, ольха)
- ⏰ Запуск по расписанию через GitHub Actions
- 💬 Команда `/check` для получения данных в любое время

## Установка

1. Клонируйте репозиторий
2. Установите зависимости:
   ```bash
   pip install requests
   ```

3. Создайте `.env` файл:
   ```bash
   cp .env.example .env
   ```

4. Отредактируйте `.env`:
   ```
   TELEGRAM_BOT_TOKEN=ваш_токен_от_@BotFather
   TELEGRAM_CHAT_ID=ваш_chat_id
   ```

## Использование

### Режим по расписанию (для GitHub Actions)
```bash
python bot.py
```
Отправляет уведомление на указанный `TELEGRAM_CHAT_ID`.

### Режим с командой `/check`
```bash
python bot.py poll
```
Бот работает постоянно и отвечает на команду `/check`.

## GitHub Actions

Добавьте в Secrets репозитория:
- `POLLEN_BOT_TOKEN`
- `POLLEN_CHAT_ID`

Бот будет отправлять уведомления каждый день в 10:00 по Минску (UTC+3).

## Данные

- **Локация:** Витебск, Беларусь
- **Источник:** [Open-Meteo Air Quality API](https://open-meteo.com/)
- **Типы пыльцы:** Берёза, Ольха
