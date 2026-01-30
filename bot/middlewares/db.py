"""Middleware для инъекции сессии БД в хендлеры."""
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import new_async_session


class DbSessionMiddleware(BaseMiddleware):
    """Передаёт сессию БД в хендлеры через data['session']."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with new_async_session() as session:
            data["session"] = session
            return await handler(event, data)
