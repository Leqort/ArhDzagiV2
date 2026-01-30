"""Кастомные фильтры для хендлеров."""
from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from bot.config import BotConfig


def _user_id_from_event(event: Message | CallbackQuery) -> int | None:
    """ID пользователя из Message или CallbackQuery."""
    user = getattr(event, "from_user", None)
    return user.id if user else None


class AdminFilter(BaseFilter):
    """Фильтр: только администраторы (id в admin_ids). Подходит для Message и CallbackQuery."""

    def __init__(self, config: BotConfig) -> None:
        self.admin_ids = config.admin_ids

    async def __call__(self, event: Message | CallbackQuery) -> bool:
        uid = _user_id_from_event(event)
        return uid is not None and uid in self.admin_ids


class StaffFilter(BaseFilter):
    """Фильтр: администратор или курьер (id в admin_ids или courier_ids)."""

    def __init__(self, config: BotConfig) -> None:
        self.admin_ids = config.admin_ids
        self.courier_ids = config.courier_ids

    async def __call__(self, message: Message) -> bool:
        if message.from_user is None:
            return False
        uid = message.from_user.id
        return uid in self.admin_ids or uid in self.courier_ids
