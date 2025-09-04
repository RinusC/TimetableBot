# Telegram Schedule Bot

## Overview

This is a Telegram bot designed to automatically fetch and send school/university schedules from electronic journal systems. The bot allows users to authenticate with their journal credentials, stores their session data, and provides daily schedule notifications at a specified time. The system is built with Python using asynchronous programming patterns for efficient handling of multiple users and web requests.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes

September 3, 2025:
- Created complete Telegram bot structure with aiogram framework
- Implemented cookie-based authentication system for electronic journals  
- Added asynchronous schedule parsing with BeautifulSoup
- Set up APScheduler for daily notifications at 7:00 AM Moscow time
- Configured file-based user data storage with JSON
- Created workflow for bot deployment

## Project Architecture  

### Core Structure
```
src/
├── main.py              # Main bot controller and Telegram handlers
├── config.py           # Configuration management and environment variables
├── schedule_parser.py  # Asynchronous web scraping for journal data
└── user_data.py       # User data persistence and cookie management

run.py                  # Application entry point
user_data/             # User data storage directory
├── users.json         # User preferences and settings
└── cookies/           # Individual user cookie files
```

### Bot Architecture
The application follows a modular design with clear separation of concerns:

- **Main Bot Controller** (`src/main.py`): Handles Telegram bot interactions and command processing
- **Configuration Management** (`src/config.py`): Centralized configuration with environment variable support
- **Schedule Parser** (`src/schedule_parser.py`): Asynchronous web scraping module for extracting schedule data from journal websites
- **User Data Manager** (`src/user_data.py`): File-based user data persistence with JSON storage
- **Launcher** (`run.py`): Application entry point with environment validation

### Data Storage
The system uses a file-based storage approach:
- **JSON Files**: User data and preferences stored in `user_data/users.json`
- **Cookie Storage**: Session cookies stored in `user_data/cookies/` directory for maintaining journal authentication
- **Local File System**: Simple, dependency-free storage solution suitable for small to medium user bases

### Authentication & Session Management
- **Cookie-based Authentication**: Stores user session cookies to maintain journal login state
- **User Isolation**: Each user's authentication data is stored separately
- **Session Persistence**: Maintains login sessions across bot restarts

### Scheduling System
- **Time-based Notifications**: Configured to send daily schedules at 07:00 Moscow time
- **Timezone Support**: Built-in timezone handling for consistent scheduling
- **Asynchronous Processing**: Non-blocking schedule fetching and message sending

### Web Scraping Architecture
- **BeautifulSoup Integration**: HTML parsing for extracting schedule data from journal websites
- **Retry Logic**: Configurable retry mechanism with timeout handling
- **Error Handling**: Graceful degradation when journal systems are unavailable

## External Dependencies

### Core Libraries
- **aiogram**: Telegram Bot API framework for asynchronous bot development
- **aiohttp**: HTTP client for asynchronous web requests to journal systems
- **BeautifulSoup4**: HTML parsing and web scraping functionality
- **asyncio**: Python's built-in asynchronous programming support

### System Requirements
- **Python Environment Variables**: BOT_TOKEN required for Telegram Bot API authentication
- **File System Access**: Read/write permissions for user data and cookie storage
- **Network Access**: Outbound HTTP/HTTPS connections to journal websites and Telegram API

### External Service Integration
- **Telegram Bot API**: Primary interface for user interactions and message delivery
- **Electronic Journal Systems**: Target websites for schedule data extraction (configurable endpoints)
- **Web Session Management**: Cookie-based authentication with external journal systems

### Configuration Dependencies
- **Environment Variables**: BOT_TOKEN, optional JOURNAL_BASE_URL and JOURNAL_SCHEDULE_ENDPOINT
- **Directory Structure**: Automatic creation of user_data and cookies directories
- **Timezone Support**: Moscow timezone (Europe/Moscow) for schedule timing