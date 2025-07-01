import os
import logging
from dotenv import load_dotenv
from quart import Quart, request, jsonify
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from regions import REGIONS  # Ваш словарь регионов
import asyncio

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

# Создаем Quart приложение
app = Quart(__name__)

# Инициализация приложения Telegram перед запуском сервера
@app.before_serving
async def startup():
    logger.info("Инициализация Telegram Application...")
    await application.initialize()
    logger.info("Telegram Application инициализировано.")

@app.route('/', methods=['POST'])
async def webhook():
    if request.headers.get('content-type') == 'application/json':
        try:
            json_data = await request.get_json()
            update = Update.de_json(json_data, application.bot)
            await application.update_queue.put(update)
            return jsonify({'status': 'ok'})
        except Exception as e:
            logger.error(f"Ошибка обработки обновления: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500
    else:
        return 'Invalid content type', 403

@app.route('/', methods=['GET'])
async def index():
    return "Telegram Bot is running!"

# Запуск через Hypercorn
if __name__ == '__main__':
    import hypercorn.asyncio
    from hypercorn.config import Config

    config = Config()
    config.bind = ["0.0.0.0:8000"]

    logger.info("Запуск сервера Hypercorn...")
    asyncio.run(hypercorn.asyncio.serve(app, config))
