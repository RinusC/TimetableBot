# Telegram Timetable Bot

## Overview
This is a Russian-language Telegram bot that helps students get their school schedule from an electronic journal (edu.gounn.ru). The bot can send daily schedule notifications and respond to user requests for current and next day schedules.

## Recent Changes
- 2025-09-03: Initial setup and import from GitHub
- Fixed undefined variable bug in main.py (days_offset parameter)
- Installed Python 3.11 and project dependencies using UV package manager
- Configured workflow to run the bot with proper token

## Project Architecture
- **Language**: Python 3.11
- **Package Manager**: UV (modern Python package manager)
- **Main Dependencies**: aiogram (Telegram bot framework), aiohttp, BeautifulSoup4, APScheduler
- **Structure**:
  - `TimetableBot/run.py` - Entry point for the bot
  - `TimetableBot/src/main.py` - Main bot logic and handlers
  - `TimetableBot/src/config.py` - Configuration settings
  - `TimetableBot/src/schedule_parser.py` - Web scraping logic for journal
  - `TimetableBot/src/user_data.py` - User data management
  - `TimetableBot/user_data/` - User cookies and data storage

## Key Features
- Cookie-based authentication with electronic journal
- Daily schedule notifications at 7:00 AM Moscow time
- Interactive keyboard interface in Russian
- Schedule parsing for today and tomorrow
- User data persistence

## Configuration
- **Bot Token**: Configured via BOT_TOKEN environment variable
- **Time Zone**: Europe/Moscow (MSK)
- **Notification Time**: 07:00 daily
- **Journal URL**: https://edu.gounn.ru

## Current Status
✅ Project successfully imported and configured
✅ Dependencies installed
✅ Bot is running and connected to Telegram
✅ Ready for user interaction