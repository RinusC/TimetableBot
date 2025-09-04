"""
Модуль для парсинга расписания из электронного журнала
"""

import aiohttp
import asyncio
import logging
from datetime import datetime, date
from typing import Optional, Dict, List, Any
from bs4 import BeautifulSoup, Tag

from .config import (
    JOURNAL_BASE_URL, 
    JOURNAL_SCHEDULE_ENDPOINT, 
    REQUEST_TIMEOUT, 
    MAX_RETRIES
)

# Настройка логирования
logger = logging.getLogger(__name__)


class ScheduleParser:
    """Класс для парсинга расписания из электронного журнала"""
    
    def __init__(self):
        self.base_url = JOURNAL_BASE_URL
        self.schedule_endpoint = JOURNAL_SCHEDULE_ENDPOINT
        self.timeout = REQUEST_TIMEOUT
        self.max_retries = MAX_RETRIES
    
    async def get_schedule(self, cookies: str, days_offset: int = 0) -> Optional[str]:
        """
        Получение расписания из электронного журнала
        
        Args:
            cookies: Куки файлы пользователя
            days_offset: Смещение в днях (0 - сегодня, 1 - завтра, и т.д.)
            
        Returns:
            Отформатированное расписание или None при ошибке
        """
        try:
            # Парсим куки в словарь
            cookie_dict = self._parse_cookies(cookies)
            
            # Получаем HTML страницу с расписанием
            html_content = await self._fetch_schedule_page(cookie_dict)
            
            if not html_content:
                logger.warning("Не удалось получить содержимое страницы расписания")
                return None
            
            # Парсим расписание из HTML
            schedule = self._parse_schedule_html(html_content, days_offset)
            
            if not schedule:
                logger.warning("Не удалось распарсить расписание из HTML")
                return None
            
            # Форматируем расписание для отправки
            formatted_schedule = self._format_schedule(schedule, days_offset)
            
            return formatted_schedule
            
        except Exception as e:
            logger.error(f"Ошибка при получении расписания: {e}")
            return None
    
    def _parse_cookies(self, cookies: str) -> Dict[str, str]:
        """
        Парсинг строки куки в словарь
        
        Args:
            cookies: Строка куки в формате "key1=value1; key2=value2"
            
        Returns:
            Словарь с куки
        """
        cookie_dict = {}
        
        try:
            for cookie in cookies.split(';'):
                cookie = cookie.strip()
                if '=' in cookie:
                    key, value = cookie.split('=', 1)
                    cookie_dict[key.strip()] = value.strip()
            
            logger.debug(f"Распарсено {len(cookie_dict)} куки")
            return cookie_dict
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге куки: {e}")
            return {}
    
    async def _fetch_schedule_page(self, cookies: Dict[str, str]) -> Optional[str]:
        """
        Получение HTML страницы с расписанием
        
        Args:
            cookies: Словарь с куки
            
        Returns:
            HTML содержимое страницы или None
        """
        url = f"{self.base_url}{self.schedule_endpoint}"
        
        # Добавляем текущую дату как параметр (может потребоваться для некоторых журналов)
        today = date.today().strftime('%Y-%m-%d')
        params = {'date': today}
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession(
                    cookies=cookies,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as session:
                    
                    async with session.get(url, headers=headers, params=params) as response:
                        if response.status == 200:
                            content = await response.text()
                            logger.info(f"Успешно получена страница расписания (попытка {attempt + 1})")
                            return content
                        else:
                            logger.warning(f"HTTP {response.status} при получении расписания (попытка {attempt + 1})")
                            
            except asyncio.TimeoutError:
                logger.warning(f"Таймаут при получении расписания (попытка {attempt + 1})")
            except Exception as e:
                logger.error(f"Ошибка при запросе расписания (попытка {attempt + 1}): {e}")
            
            if attempt < self.max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Экспоненциальная задержка
        
        logger.error("Все попытки получить расписание исчерпаны")
        return None
    
    def _parse_schedule_html(self, html_content: str, days_offset: int = 0) -> Optional[List[Dict[str, Any]]]:
        """
        Парсинг расписания из HTML для edu.gounn.ru
        Извлекаем данные из JavaScript переменной scheduleData
        
        Args:
            html_content: HTML содержимое страницы
            days_offset: Смещение в днях (0 - сегодня, 1 - завтра, и т.д.)
            
        Returns:
            Список уроков или None
        """
        try:
            import re
            import json
            from datetime import datetime, date, timedelta
            
            schedule_items = []
            
            # Ищем JavaScript переменную scheduleData в HTML
            schedule_data_pattern = r'var scheduleData = (\[.*?\]);'
            match = re.search(schedule_data_pattern, html_content, re.DOTALL)
            
            if match:
                try:
                    # Извлекаем JSON данные
                    schedule_json = match.group(1)
                    schedule_data = json.loads(schedule_json)
                    
                    logger.info(f"Найдено {len(schedule_data)} дней в расписании")
                    
                    # Вычисляем нужную дату на основе days_offset
                    target_date = (date.today() + timedelta(days=days_offset)).strftime('%Y-%m-%d')
                    
                    # Ищем расписание на нужную дату
                    for day_data in schedule_data:
                        if day_data.get('date') == target_date:
                            items = day_data.get('items', [])
                            logger.info(f"Найдено {len(items)} уроков на {target_date}")
                            
                            for item in items:
                                lesson_data = {
                                    'time': f"{item.get('starttime', '')[:5]} - {item.get('endtime', '')[:5]}",
                                    'subject': item.get('lesson', ''),
                                    'teacher': item.get('teacher', ''),
                                    'room': item.get('room', ''),
                                    'group': item.get('group_name', '')
                                }
                                
                                # Убираем пустые данные
                                lesson_data = {k: v for k, v in lesson_data.items() if v}
                                
                                if lesson_data.get('subject'):
                                    schedule_items.append(lesson_data)
                            
                            break
                    
                    if not schedule_items:
                        # Если на нужную дату нет уроков, проверяем соседние дни
                        logger.info(f"На {target_date} расписание не найдено, проверяем ближайшие дни")
                        for day_data in schedule_data[:5]:  # Проверяем первые 5 дней
                            if day_data.get('items'):
                                items = day_data.get('items', [])
                                date_formatted = day_data.get('dateFormatted', day_data.get('date', ''))
                                logger.info(f"Используем расписание на {date_formatted} ({len(items)} уроков)")
                                
                                for item in items:
                                    lesson_data = {
                                        'time': f"{item.get('starttime', '')[:5]} - {item.get('endtime', '')[:5]}",
                                        'subject': item.get('lesson', ''),
                                        'teacher': item.get('teacher', ''),
                                        'room': item.get('room', ''),
                                        'group': item.get('group_name', '')
                                    }
                                    
                                    lesson_data = {k: v for k, v in lesson_data.items() if v}
                                    
                                    if lesson_data.get('subject'):
                                        schedule_items.append(lesson_data)
                                
                                break
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Ошибка парсинга JSON: {e}")
                except Exception as e:
                    logger.error(f"Ошибка обработки данных расписания: {e}")
            
            # Если не нашли scheduleData, пробуем альтернативные методы
            if not schedule_items:
                logger.info("scheduleData не найдена, пробуем альтернативные методы")
                schedule_items = self._parse_html_fallback(html_content)
            
            if schedule_items:
                logger.info(f"Итого найдено {len(schedule_items)} уроков")
                return schedule_items
            else:
                logger.warning("Расписание не найдено")
                # Сохраняем фрагмент HTML для отладки
                with open('debug_schedule.html', 'w', encoding='utf-8') as f:
                    f.write(html_content[:3000])  # Первые 3000 символов
                return None
                
        except Exception as e:
            logger.error(f"Критическая ошибка при парсинге HTML: {e}")
            return None
    
    def _parse_html_fallback(self, html_content: str) -> List[Dict[str, Any]]:
        """
        Резервный метод парсинга HTML если scheduleData не найдена
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            schedule_items = []
            
            # Ищем таблицы с расписанием
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        text_cells = [cell.get_text(strip=True) for cell in cells]
                        
                        # Если в ячейке есть время и предмет
                        import re
                        time_pattern = re.compile(r'\d{1,2}:\d{2}')
                        
                        for i, cell_text in enumerate(text_cells):
                            if time_pattern.match(cell_text) and i + 1 < len(text_cells):
                                lesson_data = {
                                    'time': cell_text,
                                    'subject': text_cells[i + 1],
                                    'room': text_cells[i + 2] if i + 2 < len(text_cells) else '',
                                    'teacher': text_cells[i + 3] if i + 3 < len(text_cells) else ''
                                }
                                
                                if lesson_data['subject']:
                                    schedule_items.append(lesson_data)
            
            return schedule_items
            
        except Exception as e:
            logger.error(f"Ошибка в резервном парсере: {e}")
            return []
    
    def _extract_lesson_data(self, element) -> Optional[Dict[str, Any]]:
        """
        Извлечение данных урока из HTML элемента
        
        Args:
            element: BeautifulSoup элемент
            
        Returns:
            Словарь с данными урока или None
        """
        try:
            lesson_data = {}
            
            # Извлекаем время урока
            time_element = element.find(class_=['time', 'period', 'lesson-time'])
            if time_element:
                lesson_data['time'] = time_element.get_text(strip=True)
            
            # Извлекаем название предмета
            subject_element = element.find(class_=['subject', 'lesson-name', 'discipline'])
            if subject_element:
                lesson_data['subject'] = subject_element.get_text(strip=True)
            
            # Извлекаем кабинет
            room_element = element.find(class_=['room', 'cabinet', 'classroom'])
            if room_element:
                lesson_data['room'] = room_element.get_text(strip=True)
            
            # Извлекаем преподавателя
            teacher_element = element.find(class_=['teacher', 'instructor'])
            if teacher_element:
                lesson_data['teacher'] = teacher_element.get_text(strip=True)
            
            # Альтернативный способ - ищем текст по паттернам
            if not lesson_data.get('subject'):
                text = element.get_text(strip=True)
                if text and len(text) > 3:
                    # Простейшая эвристика для определения предмета
                    lesson_data['subject'] = text
            
            # Проверяем, что хотя бы предмет найден
            if lesson_data.get('subject'):
                return lesson_data
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении данных урока: {e}")
            return None
    
    def _format_schedule(self, schedule_items: List[Dict[str, Any]], days_offset: int = 0) -> str:
        """
        Форматирование расписания для отправки в Telegram
        
        Args:
            schedule_items: Список уроков
            days_offset: Смещение в днях (0 - сегодня, 1 - завтра, и т.д.)
            
        Returns:
            Отформатированная строка с расписанием
        """
        from datetime import date, timedelta
        
        if not schedule_items:
            if days_offset == 0:
                return "📅 Расписание на сегодня пустое"
            elif days_offset == 1:
                return "📅 Расписание на завтра пустое"
            else:
                return f"📅 Расписание на {days_offset} дней вперед пустое"
        
        target_date = (date.today() + timedelta(days=days_offset)).strftime('%d.%m.%Y')
        
        if days_offset == 0:
            header = f"📅 <b>Расписание на сегодня ({target_date})</b>\n"
        elif days_offset == 1:
            header = f"📅 <b>Расписание на завтра ({target_date})</b>\n"
        else:
            header = f"📅 <b>Расписание на {target_date}</b>\n"
        
        formatted_lines = [header]
        
        for i, lesson in enumerate(schedule_items, 1):
            lesson_line = f"<b>{i}.</b> "
            
            # Время урока
            if lesson.get('time'):
                lesson_line += f"⏰ {lesson['time']} - "
            
            # Предмет
            if lesson.get('subject'):
                lesson_line += f"📚 {lesson['subject']}"
            
            # Кабинет
            if lesson.get('room'):
                lesson_line += f" 🏫 Кабинет: {lesson['room']}"
            
            # Преподаватель
            if lesson.get('teacher'):
                lesson_line += f" 👨‍🏫 {lesson['teacher']}"
            
            formatted_lines.append(lesson_line)
        
        return "\n\n".join(formatted_lines)
    
    async def test_connection(self, cookies: str) -> bool:
        """
        Тестирование подключения к электронному журналу
        
        Args:
            cookies: Куки файлы пользователя
            
        Returns:
            True если подключение успешно
        """
        try:
            cookie_dict = self._parse_cookies(cookies)
            html_content = await self._fetch_schedule_page(cookie_dict)
            return html_content is not None
        except Exception as e:
            logger.error(f"Ошибка при тестировании подключения: {e}")
            return False