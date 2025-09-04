"""
Модуль для работы с пользовательскими данными и куки файлами
"""

import json
import os
from typing import Dict, Optional, Any
import logging
from .config import USER_DATA_DIR, COOKIES_DIR

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UserDataManager:
    """Класс для управления данными пользователей и их куки"""
    
    def __init__(self):
        self.users_file = os.path.join(USER_DATA_DIR, "users.json")
        self._ensure_files_exist()
    
    def _ensure_files_exist(self):
        """Создание файлов данных если они не существуют"""
        if not os.path.exists(self.users_file):
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
    
    def get_user_data(self, user_id: int) -> Dict[str, Any]:
        """Получение данных пользователя"""
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                users = json.load(f)
                return users.get(str(user_id), {})
        except Exception as e:
            logger.error(f"Ошибка при получении данных пользователя {user_id}: {e}")
            return {}
    
    def save_user_data(self, user_id: int, data: Dict[str, Any]):
        """Сохранение данных пользователя"""
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                users = json.load(f)
            
            users[str(user_id)] = data
            
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(users, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Данные пользователя {user_id} сохранены")
        except Exception as e:
            logger.error(f"Ошибка при сохранении данных пользователя {user_id}: {e}")
    
    def save_user_cookies(self, user_id: int, cookies: str):
        """Сохранение куки пользователя"""
        try:
            cookies_file = os.path.join(COOKIES_DIR, f"user_{user_id}.txt")
            with open(cookies_file, 'w', encoding='utf-8') as f:
                f.write(cookies)
            
            # Обновляем данные пользователя
            user_data = self.get_user_data(user_id)
            user_data['has_cookies'] = True
            user_data['cookies_file'] = cookies_file
            self.save_user_data(user_id, user_data)
            
            logger.info(f"Куки пользователя {user_id} сохранены")
        except Exception as e:
            logger.error(f"Ошибка при сохранении куки пользователя {user_id}: {e}")
    
    def get_user_cookies(self, user_id: int) -> Optional[str]:
        """Получение куки пользователя"""
        try:
            user_data = self.get_user_data(user_id)
            if not user_data.get('has_cookies'):
                return None
            
            cookies_file = user_data.get('cookies_file')
            if not cookies_file or not os.path.exists(cookies_file):
                return None
            
            with open(cookies_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            logger.error(f"Ошибка при получении куки пользователя {user_id}: {e}")
            return None
    
    def user_has_cookies(self, user_id: int) -> bool:
        """Проверка наличия куки у пользователя"""
        user_data = self.get_user_data(user_id)
        return user_data.get('has_cookies', False)
    
    def get_all_users_with_schedule(self) -> list:
        """Получение всех пользователей с включенным расписанием"""
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                users = json.load(f)
            
            active_users = []
            for user_id, data in users.items():
                if data.get('schedule_enabled', False) and data.get('has_cookies', False):
                    active_users.append(int(user_id))
            
            return active_users
        except Exception as e:
            logger.error(f"Ошибка при получении пользователей с расписанием: {e}")
            return []
    
    def enable_schedule(self, user_id: int):
        """Включение расписания для пользователя"""
        user_data = self.get_user_data(user_id)
        user_data['schedule_enabled'] = True
        self.save_user_data(user_id, user_data)
    
    def disable_schedule(self, user_id: int):
        """Отключение расписания для пользователя"""
        user_data = self.get_user_data(user_id)
        user_data['schedule_enabled'] = False
        self.save_user_data(user_id, user_data)