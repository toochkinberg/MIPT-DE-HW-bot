import os
import logging
import yadisk
import pandas as pd
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

YAD_TOKEN = os.getenv('YA_OAUTH')

def transfer_to_yadisk(local_file_path='data/data.xlsx', disk_file_path='/trash/data_to_dashboard/data.xlsx'):
    # Проверяем токен
    y = yadisk.YaDisk(token=YAD_TOKEN)  # Исправлено: yadisk.yadisk -> yadisk.YaDisk
    if not YAD_TOKEN:
        logger.error("Токен Яндекс.Диска (YAD_TOKEN) не указан в .env!")
        return

    if not y.check_token():
        logger.error("Токен недействителен, попробуйте получить его заново через Яндекс.Диск API.")
        return

    logger.info("Токен действителен, можно приступать к работе с файлами на Яндекс.Диске.")

    # Проверяем существование CSV-файла
    csv_file = 'data/data.csv'
    if not os.path.exists(csv_file):
        logger.error(f"CSV-файл {csv_file} не найден!")
        return

    # Конвертируем CSV в Excel
    try:
        df = pd.read_csv(csv_file)
        if df.empty:
            logger.warning("CSV-файл пуст, выгрузка не выполнена.")
            return
        df.to_excel(local_file_path, index=False)
        logger.info(f"Данные перенесены в Excel: {local_file_path}")
    except Exception as e:
        logger.error(f"Ошибка при конвертации CSV в Excel: {e}")
        return

    # Проверяем и создаём директорию на Яндекс.Диске
    try:
        # Извлекаем путь к директории из disk_file_path
        disk_dir = os.path.dirname(disk_file_path)
        if disk_dir and not y.exists(disk_dir):
            y.mkdir(disk_dir)
            logger.info(f"Создана директория на Яндекс.Диске: {disk_dir}")
    except Exception as e:
        logger.error(f"Ошибка при создании директории на Яндекс.Диске: {e}")
        return

    # Загружаем файл на Яндекс.Диск
    try:
        y.upload(local_file_path, disk_file_path, overwrite=True)
        logger.info(f"Файл {local_file_path} успешно загружен на Яндекс.Диск по пути {disk_file_path}")
    except Exception as e:
        logger.error(f"Не удалось загрузить файл на Яндекс.Диск: {e}")
        return

    # Удаляем локальный Excel-файл после загрузки
    try:
        os.remove(local_file_path)
        logger.info(f"Локальный файл {local_file_path} удалён после загрузки.")
    except Exception as e:
        logger.warning(f"Не удалось удалить локальный файл {local_file_path}: {e}")

if __name__ == "__main__":
    transfer_to_yadisk()