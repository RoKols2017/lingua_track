"""
Основной файл Telegram-бота.
Инициализация, настройка команд и запуск бота.
"""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from .config import BOT_TOKEN, BOT_COMMANDS
from .handlers import router

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def set_commands(bot: Bot):
    """Устанавливает команды бота."""
    commands = [
        BotCommand(command=cmd, description=desc)
        for cmd, desc in BOT_COMMANDS
    ]
    await bot.set_my_commands(commands)

async def main():
    """Основная функция запуска бота."""
    if not BOT_TOKEN:
        logger.error("Не установлен TELEGRAM_BOT_TOKEN в переменных окружения!")
        return
    
    # Инициализация бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Подключаем роутер с обработчиками
    dp.include_router(router)
    
    # Устанавливаем команды бота
    await set_commands(bot)
    
    logger.info("Бот запускается...")
    
    try:
        # Запускаем бота
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main()) 