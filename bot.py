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
import time

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
def log_to_csv(user_id: int, action: str, request_length: int = 0, response_length: int = 0, processing_time: float = 0.0) -> None:
    try:
        curr_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

        # Данные для логирования
        data = {
            'id': [user_id],
            'datetime': [curr_time],
            'action': [action],
            'request_length': [request_length],
            'response_length': [response_length],
            'processing_time': [processing_time]
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

    start_time = time.time()

    start_time = time.time()

    response_text = f"""Hi, {user.mention_html()}! Я чат-бот на основе YaGPT 🧐

Можешь задавать мне любые вопросы, а я постараюсь на них ответить!

Команды в чате:
/start - котик и это сообщение
/joke - надорвать животик
/help - неотложка"""
    
    await update.message.reply_html(
        response_text,
        reply_markup=ForceReply(selective=True),
    )
    try:
        await update.message.reply_sticker(sticker='CAACAgIAAxkBAAMgaAQSmFjk_8_YuLwz6hUVsvPPiKIAAphNAAKJsilJ5BhCB1jHD1g2BA')
        logger.info(f"Отправлен стикер {'CAACAgIAAxkBAAMgaAQSmFjk_8_YuLwz6hUVsvPPiKIAAphNAAKJsilJ5BhCB1jHD1g2BA'} пользователю {user_id}")
    except Exception as e:
        logger.error(f"Ошибка отправки стикера: {e}")

    # Время обработки
    processing_time = time.time() - start_time
    
    # Логируем: запроса нет (команда), длина ответа — длина текста + стикер (если есть)
    log_to_csv(
        user_id=user_id,
        action='Start',
        request_length=0,
        response_length=len(response_text),
        processing_time=processing_time
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    user_id = update.message.from_user.id
    logger.info(f"Команда /help от {user_id}")

    # Замеряем время обработки
    start_time = time.time()

    response_text = """Команды в боте:
    Почитать ленивое приветствие и посмотреть на котика: /start
    Получить "смешную" шутеечку: /joke
    ПОМОЩЬ!!!!: /help"""
    await update.message.reply_text(response_text)

    # Время обработки
    processing_time = time.time() - start_time

    # Логируем: запроса нет (команда), длина ответа — длина текста
    log_to_csv(
        user_id=user_id,
        action='Help',
        request_length=0,
        response_length=len(response_text),
        processing_time=processing_time
    )


async def joke_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a joke when the command /joke is issued."""
    user_id = update.message.from_user.id
    logger.info(f"Команда /joke от {user_id}")

    # Замеряем время обработки
    start_time = time.time()

    # Фиксированный запрос для анекдота
    user_text = "Чат, расскажи смешной анекдот"
    try:
        # Получаем IAM токен
        iam_token = get_iam_token()

        # Собираем запрос
        data = {
            "modelUri": f"gpt://{FOLDER_ID}/yandexgpt",
            "completionOptions": {"temperature": 0.3, "maxTokens": 1000},
            "messages": [{"role": "user", "text": user_text}]
        }

        URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        # Отправляем запрос
        response = requests.post(
            URL,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {iam_token}"
            },
            json=data,
        )
        response.raise_for_status()
        response_data = response.json()

        # Извлекаем ответ
        answer = response_data.get('result', {})\
                             .get('alternatives', [{}])[0]\
                             .get('message', {})\
                             .get('text', 'Не удалось рассказать анекдот.')

        await update.message.reply_text(answer)
    except requests.RequestException as e:
        logger.error(f"Ошибка запроса к Yandex GPT: {e}")
        answer = "Ошибка при получении анекдота."
        await update.message.reply_text(answer)

    # Время обработки
    processing_time = time.time() - start_time

    # Логируем: длина запроса — длина фиксированного текста, длина ответа — длина ответа
    log_to_csv(
        user_id=user_id,
        action='Joke',
        request_length=len(user_text),
        response_length=len(answer),
        processing_time=processing_time
    )


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
    logger.info(f"Получено сообщение: {user_text} от {user_id}")

    # Замеряем время обработки
    start_time = time.time()

    try:
        # Получаем IAM токен
        iam_token = get_iam_token()

        # Собираем запрос
        data = {
            "modelUri": f"gpt://{FOLDER_ID}/yandexgpt",
            "completionOptions": {"temperature": 0.3, "maxTokens": 1000},
            "messages": [{"role": "user", "text": user_text}]
        }

        URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        # Отправляем запрос
        response = requests.post(
            URL,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {iam_token}"
            },
            json=data,
        )
        response.raise_for_status()
        response_data = response.json()

        # Извлекаем ответ
        answer = response_data.get('result', {})\
                             .get('alternatives', [{}])[0]\
                             .get('message', {})\
                             .get('text', 'Ошибка: ответ не получен.')

        await update.message.reply_text(answer)
    except requests.RequestException as e:
        logger.error(f"Ошибка запроса к Yandex GPT: {e}")
        answer = "Ошибка при обработке запроса."
        await update.message.reply_text(answer)

    # Время обработки
    processing_time = time.time() - start_time

    # Логируем: длина запроса — длина текста пользователя, длина ответа — длина ответа
    log_to_csv(
        user_id=user_id,
        action='Answer',
        request_length=len(user_text),
        response_length=len(answer),
        processing_time=processing_time
    )


def main() -> None:
    """Start the bot."""
    logger.info("Запуск бота...")

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TG_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("joke", joke_command))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_message))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()