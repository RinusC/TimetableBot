#!/usr/bin/env python3
"""
Файл запуска Telegram бота
"""

import os
import sys
sys.path.insert(0, './src')
from src.main import TelegramBot

def setup_environment():
    """Настройка переменных окружения"""
    # Импортируем токен из config.py
    from src.config import BOT_TOKEN
    
    if not BOT_TOKEN:
        print("❌ ОШИБКА: BOT_TOKEN не найден!")
        sys.exit(1)
    
    # Устанавливаем значения по умолчанию для настроек электронного журнала
    if not os.getenv('JOURNAL_BASE_URL'):
        os.environ['JOURNAL_BASE_URL'] = "https://journal.example.com"
    
    if not os.getenv('JOURNAL_SCHEDULE_ENDPOINT'):
        os.environ['JOURNAL_SCHEDULE_ENDPOINT'] = "/api/schedule"
    
    print("✅ Переменные окружения настроены")
    print(f"Bot Token: {BOT_TOKEN[:10]}***")

def main():
    """Основная функция запуска"""
    print("🤖 Запуск Telegram бота для расписания...")
    
    try:
        # Настройка переменных окружения
        setup_environment()
        
        # Создание и запуск бота
        bot = TelegramBot()
        
        import asyncio
        asyncio.run(bot.start_bot())
        
    except KeyboardInterrupt:
        print("\n🔴 Бот остановлен пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Критическая ошибка при запуске бота: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()