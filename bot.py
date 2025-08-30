import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import os

# === Загружаем переменные окружения из .env ===
load_dotenv()

# === ТОКЕН БОТА ===
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("Токен не найден! Убедитесь, что файл .env существует и содержит TELEGRAM_BOT_TOKEN")

# === Импорт региональных данных из соседнего файла ===
from regions import REGIONS

# === Обратный словарь: код → название (для поиска по цифрам) ===
CODE_TO_NAME = {code: name for code, name in REGIONS.items()}

# === Функция нормализации названия ===
def normalize_name(name):
    prefixes = ["город", "область", "республика", "край", "автономная", "автономный"]
    for prefix in prefixes:
        name = name.replace(prefix, "")
    return name.strip().lower()

# === Словарь: нормализованное название → код (для поиска по тексту) ===
NAME_TO_CODE = {}
for code, name in REGIONS.items():
    normalized = normalize_name(name)
    NAME_TO_CODE[normalized] = code
    short_name = normalized.split(',')[0].split(' ')[0]
    if short_name != normalized:
        NAME_TO_CODE[short_name] = code

# === Настройка логирования ===
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# === Команда /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Введите часть названия региона или код (например, 77 или мос) для поиска."
    )

# === Обработка сообщений ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = normalize_name(update.message.text.strip())

    # 1. Если это цифровой код региона
    if user_input.isdigit():
        if user_input in CODE_TO_NAME:
            await update.message.reply_text(f"Код {user_input} — это {CODE_TO_NAME[user_input]}")
        else:
            await update.message.reply_text("Регион с таким кодом не найден.")
        return

    # 2. Поиск по названию региона (с нормализацией)
    matches = []
    for name_normalized, code in NAME_TO_CODE.items():
        if user_input in name_normalized:
            region_full_name = REGIONS[code]
            matches.append(f"{region_full_name} ({code})")

    if not matches:
        await update.message.reply_text("Совпадений не найдено.")
    elif len(matches) == 1:
        await update.message.reply_text(matches[0])
    else:
        result = "\n".join(matches[:5])
        if len(matches) > 5:
            result += "\n... и другие"
        await update.message.reply_text(result)

# === Запуск бота ===
def main():
    print("Бот запускается...")
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен. Ожидание сообщений...")
    application.run_polling()

if __name__ == '__main__':
    main()
