"""
Конфигурационный файл для Telegram бота
"""

import os
from typing import Optional

# Настройки Telegram бота
BOT_TOKEN: Optional[str] = os.getenv('BOT_TOKEN')

# Настройки времени
SCHEDULE_TIME = "07:00"  # Время отправки расписания (МСК)
TIMEZONE = "Europe/Moscow"

# Настройки файлов
USER_DATA_DIR = "user_data"
COOKIES_DIR = os.path.join(USER_DATA_DIR, "cookies")

# Создание необходимых директорий
os.makedirs(USER_DATA_DIR, exist_ok=True)
os.makedirs(COOKIES_DIR, exist_ok=True)

# Настройки электронного журнала
JOURNAL_BASE_URL = "https://edu.gounn.ru"
JOURNAL_SCHEDULE_ENDPOINT = "/journal-schedule-action"

# Настройки парсинга
REQUEST_TIMEOUT = 30  # Таймаут для HTTP запросов
MAX_RETRIES = 3  # Максимальное количество попыток запроса