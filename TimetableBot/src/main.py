"""
Telegram бот для отправки расписания из электронного журнала
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from config import BOT_TOKEN, SCHEDULE_TIME, TIMEZONE
from user_data import UserDataManager
from schedule_parser import ScheduleParser

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Состояния FSM для ввода куки
class UserStates(StatesGroup):
    waiting_for_cookies = State()

# Клавиатуры
def get_main_keyboard():
    """Главная клавиатура бота"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📚 Расписание на сегодня"), KeyboardButton(text="📅 Расписание на завтра")],
            [KeyboardButton(text="🔧 Настроить куки")],
            [KeyboardButton(text="⏰ Включить уведомления"), KeyboardButton(text="🔕 Отключить уведомления")],
            [KeyboardButton(text="ℹ️ Помощь")]
        ],
        resize_keyboard=True
    )
    return keyboard

class TelegramBot:
    """Основной класс Telegram бота"""
    
    def __init__(self):
        if not BOT_TOKEN:
            raise ValueError("BOT_TOKEN не установлен! Укажите токен бота в переменных окружения.")
        
        self.bot = Bot(token=BOT_TOKEN)
        self.dp = Dispatcher(storage=MemoryStorage())
        self.user_manager = UserDataManager()
        self.schedule_parser = ScheduleParser()
        self.scheduler = AsyncIOScheduler(timezone=pytz.timezone(TIMEZONE))
        
        # Регистрация обработчиков
        self._register_handlers()
        
        # Настройка планировщика
        self._setup_scheduler()
    
    def _register_handlers(self):
        """Регистрация всех обработчиков команд"""
        self.dp.message.register(self.cmd_start, Command("start"))
        self.dp.message.register(self.cmd_help, Command("help"))
        self.dp.message.register(self.handle_cookies_input, StateFilter(UserStates.waiting_for_cookies))
        self.dp.message.register(self.handle_text_messages, F.text)
    
    def _setup_scheduler(self):
        """Настройка планировщика для отправки расписания"""
        hour, minute = map(int, SCHEDULE_TIME.split(':'))
        
        self.scheduler.add_job(
            self.send_schedule_to_all,
            CronTrigger(hour=hour, minute=minute, timezone=pytz.timezone(TIMEZONE)),
            id='daily_schedule',
            replace_existing=True
        )
        
        logger.info(f"Планировщик настроен на {SCHEDULE_TIME} ({TIMEZONE})")
    
    async def cmd_start(self, message: Message):
        """Обработчик команды /start"""
        if not message.from_user:
            return
        
        user_id = message.from_user.id
        username = message.from_user.username or message.from_user.first_name or "Пользователь"
        
        # Сохраняем базовую информацию о пользователе
        user_data = self.user_manager.get_user_data(user_id)
        user_data.update({
            'username': username,
            'first_name': message.from_user.first_name or "Пользователь",
            'last_seen': datetime.now().isoformat()
        })
        self.user_manager.save_user_data(user_id, user_data)
        
        welcome_text = (
            f"👋 Привет, {username}!\n\n"
            "Я бот для получения расписания из электронного журнала.\n\n"
            "📋 Что я умею:\n"
            "• Показывать ваше расписание на сегодня\n"
            "• Присылать расписание каждое утро в 7:00 МСК\n"
            "• Показывать номера кабинетов\n\n"
            "⚙️ Для начала работы нужно настроить куки файлы от электронного журнала.\n"
            "Используйте кнопку \"🔧 Настроить куки\" или команду /help для подробной инструкции."
        )
        
        await message.answer(welcome_text, reply_markup=get_main_keyboard())
    
    async def cmd_help(self, message: Message):
        """Обработчик команды /help"""
        help_text = (
            "📖 <b>Инструкция по использованию бота</b>\n\n"
            
            "🔧 <b>Настройка куки:</b>\n"
            "1. Откройте электронный журнал в браузере\n"
            "2. Войдите в свой аккаунт\n"
            "3. Откройте расширение EditThisCookie\n"
            "4. Скопируйте куки в формате cookie=значение\n"
            "5. Нужны: ej-esia_v2; jwt_v_2; ej_id;\n"
            "6. Также нужны: CSRF-TOKEN; ej_check\n"
            "7. Вставьте куки через точку с запятой ;\n"
            "8. Отправьте куки боту через кнопку \"🔧 Настроить куки\"\n\n"
            
            "📚 <b>Использование:</b>\n"
            "• \"📚 Расписание на сегодня\" - получить расписание на сегодня\n"
            "• \"📅 Расписание на завтра\" - получить расписание на следующий день\n"
            "• \"⏰ Включить уведомления\" - получать расписание каждое утро\n"
            "• \"🔕 Отключить уведомления\" - отключить автоматические уведомления\n\n"
            
            "⚠️ <b>Важно:</b>\n"
            "Куки файлы могут устаревать. При проблемах обновите их заново."
        )
        
        await message.answer(help_text, parse_mode="HTML")
    
    async def handle_text_messages(self, message: Message, state: FSMContext):
        """Обработчик текстовых сообщений"""
        if not message.from_user or not message.text:
            return
        
        text = message.text
        user_id = message.from_user.id
        
        if text in ["📚 Проверить расписание", "📚 Расписание на сегодня"]:
            await self.check_schedule(message, days_offset=0)
        
        elif text == "📅 Расписание на завтра":
            await self.check_schedule(message, days_offset=1)
        
        elif text == "🔧 Настроить куки":
            await self.setup_cookies(message, state)
        
        elif text == "⏰ Включить уведомления":
            await self.enable_notifications(message)
        
        elif text == "🔕 Отключить уведомления":
            await self.disable_notifications(message)
        
        elif text == "ℹ️ Помощь":
            await self.cmd_help(message)
        
        else:
            await message.answer("Используйте кнопки меню или команды для взаимодействия с ботом.")
    
    async def setup_cookies(self, message: Message, state: FSMContext):
        """Начало процесса настройки куки"""
        instruction_text = (
            "🔧 <b>Настройка куки файлов</b>\n\n"
            "Отправьте мне куки из электронного журнала в следующем формате:\n\n"
            "<code>session_id=abc123; auth_token=xyz789; user_data=example</code>\n\n"
            "💡 Подробная инструкция доступна через команду /help"
        )
        
        await message.answer(instruction_text, parse_mode="HTML")
        await state.set_state(UserStates.waiting_for_cookies)
    
    async def handle_cookies_input(self, message: Message, state: FSMContext):
        """Обработка ввода куки"""
        if not message.from_user or not message.text:
            return
        
        cookies = message.text.strip()
        user_id = message.from_user.id
        
        if not cookies or len(cookies) < 10:
            await message.answer("❌ Куки слишком короткие. Проверьте правильность ввода.")
            return
        
        # Сохраняем куки
        self.user_manager.save_user_cookies(user_id, cookies)
        
        await message.answer(
            "✅ Куки успешно сохранены!\n"
            "Теперь вы можете проверить расписание и включить уведомления.",
            reply_markup=get_main_keyboard()
        )
        
        await state.clear()
    
    async def check_schedule(self, message: Message, days_offset: int = 0):
        """Проверка расписания пользователя
        
        Args:
            message: Сообщение пользователя
            days_offset: Смещение в днях (0 - сегодня, 1 - завтра, и т.д.)
        """
        if not message.from_user:
            return
        
        user_id = message.from_user.id
        
        if not self.user_manager.user_has_cookies(user_id):
            await message.answer(
                "❌ Сначала настройте куки файлы!\n"
                "Используйте кнопку \"🔧 Настроить куки\""
            )
            return
        
        if days_offset == 0:
            await message.answer("🔄 Получаю расписание на сегодня...")
        elif days_offset == 1:
            await message.answer("🔄 Получаю расписание на завтра...")
        else:
            await message.answer(f"🔄 Получаю расписание на {days_offset} дней вперед...")
        
        try:
            cookies = self.user_manager.get_user_cookies(user_id)
            if not cookies:
                await message.answer(
                    "❌ Куки не найдены. Настройте куки файлы!"
                )
                return
            
            schedule = await self.schedule_parser.get_schedule(cookies, days_offset=days_offset)
            
            if schedule:
                await message.answer(schedule, parse_mode="HTML")
            else:
                await message.answer(
                    "❌ Не удалось получить расписание.\n"
                    "Возможно, куки устарели. Попробуйте обновить их."
                )
        
        except Exception as e:
            logger.error(f"Ошибка при получении расписания для пользователя {user_id}: {e}")
            await message.answer(
                "❌ Произошла ошибка при получении расписания.\n"
                "Проверьте настройки и попробуйте позже."
            )
    
    async def enable_notifications(self, message: Message):
        """Включение уведомлений"""
        if not message.from_user:
            return
        
        user_id = message.from_user.id
        
        if not self.user_manager.user_has_cookies(user_id):
            await message.answer(
                "❌ Сначала настройте куки файлы!\n"
                "Используйте кнопку \"🔧 Настроить куки\""
            )
            return
        
        self.user_manager.enable_schedule(user_id)
        
        await message.answer(
            f"✅ Уведомления включены!\n"
            f"Каждый день в {SCHEDULE_TIME} (МСК) я буду присылать вам расписание."
        )
    
    async def disable_notifications(self, message: Message):
        """Отключение уведомлений"""
        if not message.from_user:
            return
        
        user_id = message.from_user.id
        self.user_manager.disable_schedule(user_id)
        
        await message.answer("🔕 Уведомления отключены.")
    
    async def send_schedule_to_all(self):
        """Отправка расписания всем активным пользователям"""
        active_users = self.user_manager.get_all_users_with_schedule()
        
        logger.info(f"Отправка расписания {len(active_users)} пользователям")
        
        for user_id in active_users:
            try:
                cookies = self.user_manager.get_user_cookies(user_id)
                if not cookies:
                    continue
                
                schedule = await self.schedule_parser.get_schedule(cookies, days_offset=days_offset)
                
                if schedule:
                    await self.bot.send_message(
                        user_id,
                        f"🌅 <b>Доброе утро! Ваше расписание на сегодня:</b>\n\n{schedule}",
                        parse_mode="HTML"
                    )
                    logger.info(f"Расписание отправлено пользователю {user_id}")
                else:
                    await self.bot.send_message(
                        user_id,
                        "❌ Не удалось получить расписание. Проверьте настройки куки."
                    )
            
            except Exception as e:
                logger.error(f"Ошибка при отправке расписания пользователю {user_id}: {e}")
    
    async def start_bot(self):
        """Запуск бота"""
        try:
            # Запуск планировщика
            self.scheduler.start()
            logger.info("Планировщик запущен")
            
            # Запуск бота
            logger.info("Запуск Telegram бота...")
            await self.dp.start_polling(self.bot)
            
        except Exception as e:
            logger.error(f"Ошибка при запуске бота: {e}")
        finally:
            await self.bot.session.close()


if __name__ == "__main__":
    try:
        bot = TelegramBot()
        asyncio.run(bot.start_bot())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")