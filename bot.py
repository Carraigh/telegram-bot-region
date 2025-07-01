import os
import logging
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from regions import REGIONS  # Ваш словарь регионов

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN не найден в .env файле!")
    raise ValueError("TELEGRAM_BOT_TOKEN не установлен")

# Нормализация текста
def normalize(text: str) -> str:
    return text.lower().strip()

# Создаем приложение Telegram
application = ApplicationBuilder().token(TOKEN).build()

# Обработчики команд
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Введите часть названия региона или код для поиска.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = normalize(update.message.text)

    if user_input in REGIONS:
        await update.message.reply_text(f"Код {user_input} — это {REGIONS[user_input]}")
        return

    matches = []
    for code, name in REGIONS.items():
        if user_input in normalize(name):
            matches.append(f"{name} ({code})")

    if not matches:
        await update.message.reply_text("Совпадений не найдено.")
    elif len(matches) == 1:
        await update.message.reply_text(matches[0])
    else:
        reply = "\n".join(matches[:5])
        if len(matches) > 5:
            reply += "\n... и другие"
        await update.message.reply_text(reply)

# Регистрация обработчиков
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Создаем Flask приложение
app = Flask(__name__)

@app.route('/', methods=['POST'])
def webhook():  # Синхронная функция (без async)
    if request.headers.get('content-type') == 'application/json':
        try:
            json_data = request.get_json(force=True)
            update = Update.de_json(json_data, application.bot)
            
            # Ключевое исправление: используем очередь вместо await
            application.update_queue.put(update)
            
            return jsonify({'status': 'ok'})
        except Exception as e:
            logger.error(f"Ошибка обработки обновления: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500
    else:
        return 'Invalid content type', 403

@app.route('/', methods=['GET'])
def index():
    return "Telegram Bot is running!"

# Для запуска через Hypercorn/Gunicorn
if __name__ == '__main__':
    # В production используйте: hypercorn bot:app --bind 0.0.0.0:$PORT
    app.run(host='0.0.0.0', port=8000, debug=True)
