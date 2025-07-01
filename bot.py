import os
import logging

from dotenv import load_dotenv
from flask import Flask, request

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from regions import REGIONS

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Загрузка токена из .env или окружения
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    raise ValueError("Не найден TELEGRAM_BOT_TOKEN в переменных окружения!")

# Функция нормализации текста
def normalize(text: str) -> str:
    return text.lower().strip()

# Обратный словарь: {region_name: code}
REVERSE_REGIONS = {}
for code, name in REGIONS.items():
    REVERSE_REGIONS[normalize(name)] = code
    short_name = name.split(',')[0].split(' ')[0].lower()
    if short_name != name.lower():
        REVERSE_REGIONS[normalize(short_name)] = code

# Создаем приложение
application = ApplicationBuilder().token(TOKEN).build()

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Введите часть названия региона или код для поиска.")

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = normalize(update.message.text)

    # Проверяем, есть ли такой код
    if user_input in REGIONS:
        region_name = REGIONS[user_input]
        await update.message.reply_text(f'Код {user_input} — это {region_name}')
        return

    # Поиск по названию
    matches = []
    for code, name in REGIONS.items():
        if user_input in normalize(name):
            matches.append(f'{name} ({code})')

    if not matches:
        await update.message.reply_text('Совпадений не найдено.')
    elif len(matches) == 1:
        await update.message.reply_text(matches[0])
    else:
        result = '\n'.join(matches[:5])
        if len(matches) > 5:
            result += "\n... и другие"
        await update.message.reply_text(result)

# Добавляем обработчики
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Flask-приложение
app = Flask(__name__)

@app.route('/', methods=['POST'])
def webhook():
    """Telegram будет отправлять апдейты сюда"""
    if request.headers.get('content-type') == 'application/json':
        json_data = request.get_json(force=True)
        update = Update.de_json(json_data, application.bot)
        application.process_update(update)
        return 'OK', 200
    else:
        return 'Invalid content type', 403

@app.route('/', methods=['GET'])
def index():
    return "Бот работает!"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8443))  # Используем PORT от Render
    app.run(host='0.0.0.0', port=port)
