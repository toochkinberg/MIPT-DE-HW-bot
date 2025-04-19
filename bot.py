"""
Simple Bot to reply to Telegram messages.

First, a few handler functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

import requests
import os
from dotenv import load_dotenv

import pandas as pd
from datetime import datetime

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

load_dotenv()

OAUTH_TOKEN = os.getenv('OAUTH')
TG_TOKEN = os.getenv('BOT_TOKEN')
FOLDER_ID = os.getenv('FOLDER_ID')

CSV_FILE = 'data/data.csv'
# Логирование действий юзера в csv
def log_to_csv(user_id: int, action: str) -> None:
    try:
        curr_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

        # Данные для логирования
        data = {
            'id' : [user_id],
            'datetime' : [curr_time],
            'action' : [action]
        }

        df = pd.DataFrame(data)

        # Если нет файла, то создаём и пишем в него, а если есть, просто пишем
        if os.path.exists(CSV_FILE):
            df.to_csv(CSV_FILE, mode='a', header=False, index=False)
        else:
            df.to_csv(CSV_FILE, mode='w', header=True, index=False)

        logger.info(f"Действие '{action}' пользователя {user_id} записано в {CSV_FILE}")
    except Exception as e:
        logger.error(f"Ошибка записи в CSV: {e}")

# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    user_id = update.message.from_user.id
    logger.info(f"Команда /start от {user.id}")

    log_to_csv(user_id=user_id, action='Start')
    await update.message.reply_html(
        rf"""Hi, {user.mention_html()}! Я чат-бот на основе YaGPT 🧐

Можешь задавать мне любые вопросы, а я постараюсь на них ответить!""",
        reply_markup=ForceReply(selective=True),
    )
    try:
            await update.message.reply_sticker(sticker='CAACAgIAAxkBAAMgaAQSmFjk_8_YuLwz6hUVsvPPiKIAAphNAAKJsilJ5BhCB1jHD1g2BA')
            logger.info(f"Отправлен стикер {'CAACAgIAAxkBAAMgaAQSmFjk_8_YuLwz6hUVsvPPiKIAAphNAAKJsilJ5BhCB1jHD1g2BA'} пользователю {user_id}")
    except Exception as e:
            logger.error(f"Ошибка отправки стикера: {e}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    log_to_csv(user_id=update.message.from_user.id, action='Help')
    await update.message.reply_text("Никто Вам не поможет(")


def get_iam_token():
    response = requests.post(
        'https://iam.api.cloud.yandex.net/iam/v1/tokens',
        json={'yandexPassportOauthToken': OAUTH_TOKEN}
    )

    response.raise_for_status()
    return response.json()['iamToken']


async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_text = update.message.text
    user_id = update.message.from_user.id
    logger.info(f"Получено сообщение: {user_text} от {update.effective_user.id}")

    log_to_csv(user_id=user_id, action='Answer')

    # Получаем IAM токен
    iam_token = get_iam_token()

    # Собираем запрос
    data = {}
    # Указываем тип модели
    data["modelUri"] = f"gpt://{FOLDER_ID}/yandexgpt"
    # Настраиваем опции
    data["completionOptions"] = {"temperature": 0.3, "maxTokens": 1000}
    # Указываем контекст для модели
    data["messages"] = [
        {"role": "user", "text": f"{user_text}"},
    ]

    URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    # Отправляем запрос
    response = requests.post(
        URL,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {iam_token}"
        },
        json=data,
    ).json()

    # Распечатываем результат
    print(response)

    answer = response.get('result', {})\
                     .get('alternatives', [{}])[0]\
                     .get('message', {})\
                     .get('text', {})

    await update.message.reply_text(answer)


def main() -> None:
    """Start the bot."""
    logger.info("Запуск бота...")

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TG_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_message))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()