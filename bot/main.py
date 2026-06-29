"""
Точка входа в приложение Telegram Bot Finder.
Запускает aiogram bot + подключает Telethon client.
"""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import load_config
from bot.handlers.start import router as start_router
from bot.handlers.search import router as search_router
from bot.handlers.summary import router as summary_router
from bot.handlers.settings import router as settings_router
from bot.services.telegram_client import TelegramClientService
from bot.services.llm_service import LLMService
from bot.storage.database import Database
from bot.middleware.auth import AuthMiddleware

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Основная функция запуска бота."""
    logger.info("Загрузка конфигурации...")
    config = load_config()

    logger.info("Инициализация базы данных...")
    db = Database(config.database_path)
    await db.initialize()

    logger.info("Инициализация Telethon client...")
    telegram_client = TelegramClientService(
        session_path="data/telegram_session",
        api_id=config.api_id,
        api_hash=config.api_hash,
        phone_number=config.phone_number,
    )
    await telegram_client.start()

    logger.info("Инициализация LLM сервиса...")
    llm_service = LLMService(
        default_provider=config.default_ai_provider,
        openai_api_key=config.openai_api_key,
        gemini_api_key=config.gemini_api_key,
        anthropic_api_key=config.anthropic_api_key,
        deepseek_api_key=config.deepseek_api_key,
        openrouter_api_key=config.openrouter_api_key,
        ollama_api_base=config.ollama_api_base,
        ollama_model=config.ollama_model,
        custom_api_base=config.custom_api_base,
        custom_api_key=config.custom_api_key,
        custom_model=config.custom_model,
    )

    logger.info("Инициализация aiogram бота...")
    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Пробрасываем зависимости в контекст диспетчера
    dp["config"] = config
    dp["telegram_client"] = telegram_client
    dp["llm_service"] = llm_service
    dp["db"] = db

    # Регистрируем middleware
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())

    # Регистрируем роутеры
    dp.include_router(start_router)
    dp.include_router(search_router)
    dp.include_router(summary_router)
    dp.include_router(settings_router)

    logger.info("Бот запущен и готов к работе!")
    try:
        await dp.start_polling(bot)
    finally:
        logger.info("Остановка бота...")
        await telegram_client.stop()
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.exception(f"Критическая ошибка: {e}")
        sys.exit(1)
