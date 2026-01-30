import asyncio
import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from config import setup_logging

setup_logging()

from database.db import Base, engine
from routes import items, flavors

from bot.bot import create_bot_and_dispatcher, run_polling
from bot.config import BotConfig

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    bot_task = None
    bot_instance = None
    config = BotConfig.from_env()
    if config.token:
        bot_instance, dp = create_bot_and_dispatcher(config)
        bot_task = asyncio.create_task(run_polling(bot_instance, dp))
        logger.info("Телеграм-бот запущен")
    else:
        logger.warning("TELEGRAM_BOT_TOKEN не задан — бот не запущен")

    yield

    if bot_task is not None:
        bot_task.cancel()
        try:
            await bot_task
        except asyncio.CancelledError:
            pass
    if bot_instance is not None:
        await bot_instance.session.close()
    await engine.dispose()


app = FastAPI(lifespan=lifespan)


app.mount("/static", StaticFiles(directory="uploads"), name="static")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# routes
app.include_router(items.router)
app.include_router(flavors.router)


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )