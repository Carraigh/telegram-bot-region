import logging
import os
from dotenv import load_dotenv

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Введите часть названия региона или код для поиска.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = normalize(update.message.text)

    # Проверяем, есть ли такой код
    if user_input in REGIONS:
        region_name = REGIONS[user_input]
        await update.message.reply_text(f'Код {user_input} — это {region_name}')
        return

    # Поиск по названию (исправлено: перебираем code, name)
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

def main():
    print("Бот готов к запуску.")
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Запуск бота...")
    application.run_polling()

if __name__ == '__main__':
    main()
