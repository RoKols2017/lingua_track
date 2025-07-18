#!/usr/bin/env python3
"""
Скрипт для запуска Telegram-бота и HTTP endpoint для Celery-уведомлений.
Запускает бота с обработкой ошибок и логированием.
"""
import sys
import os
import asyncio

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from t_bot.bot import main
from t_bot.handlers import setup_notify_endpoint

if __name__ == "__main__":
    try:
        from aiohttp import web
        # Запуск Telegram-бота и aiohttp web-сервера параллельно
        async def start_all():
            # Запуск бота в фоне
            bot_task = asyncio.create_task(main())
            # Запуск aiohttp web-сервера
            app = web.Application()
            setup_notify_endpoint(app)
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, '0.0.0.0', 8080)
            await site.start()
            print("[INFO] HTTP endpoint /notify запущен на :8080")
            await bot_task  # Ждём завершения бота
        asyncio.run(start_all())
    except ImportError:
        # Если aiohttp не установлен — просто запускаем бота
        asyncio.run(main()) 