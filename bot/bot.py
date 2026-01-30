import asyncio
import logging
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from dotenv import load_dotenv

load_dotenv(root / ".env")

from config import setup_logging

setup_logging()

from aiogram import Bot, Dispatcher, Router
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import BotConfig
from bot.handlers import setup_handlers
from bot.middlewares.db import DbSessionMiddleware

logger = logging.getLogger(__name__)


def create_bot_and_dispatcher(config: BotConfig) -> tuple[Bot, Dispatcher]:
    """Создаёт экземпляры Bot и Dispatcher с подключёнными middleware и хендлерами."""
    bot = Bot(token=config.token)
    dp = Dispatcher(storage=MemoryStorage())
    dp.message.middleware(DbSessionMiddleware())
    dp.callback_query.middleware(DbSessionMiddleware())
    router = Router()
    setup_handlers(router, config)
    dp.include_router(router)
    return bot, dp


async def run_polling(bot: Bot, dp: Dispatcher) -> None:
    """Запуск long polling (для использования как фоновая задача)."""
    await dp.start_polling(bot)


async def main() -> None:
    config = BotConfig.from_env()
    if not config.token:
        logger.error("TELEGRAM_BOT_TOKEN или TOKEN не задан в окружении")
        return

    bot, dp = create_bot_and_dispatcher(config)
    logger.info("Бот запущен")
    await run_polling(bot, dp)


if __name__ == "__main__":
    asyncio.run(main())
