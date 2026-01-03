import asyncio
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from loguru import logger

from config.settings import settings
from bot.database.crud import init_db
from bot.handlers import start, enhanced, help
# pools и strategies отключены - используется enhanced
# from bot.handlers import pools, strategies


# Настройка логирования
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO"
)
logger.add(
    "logs/bot.log",
    rotation="10 MB",
    retention="7 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
    level="DEBUG"
)


async def on_startup():
    """Выполняется при запуске бота"""
    logger.info("Bot is starting up...")
    
    # Инициализация базы данных
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    logger.info("Bot started successfully!")


async def on_shutdown():
    """Выполняется при остановке бота"""
    logger.info("Bot is shutting down...")


async def main():
    """Главная функция запуска бота"""
    # Создаем бота и диспетчер
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    
    # Регистрируем обработчики
    dp.include_router(start.router)
    dp.include_router(help.router)  # Справка должна быть перед другими, чтобы не конфликтовать
    # pools.router и strategies.router отключены - используются handlers из enhanced.router
    # dp.include_router(pools.router)
    # dp.include_router(strategies.router)
    dp.include_router(enhanced.router)  # Улучшенные handlers
    
    # Регистрируем startup и shutdown
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    try:
        # Запускаем polling
        logger.info("Starting bot polling...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error during polling: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot interrupted")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

