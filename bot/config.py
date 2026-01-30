"""Конфигурация телеграм-бота."""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class BotConfig:
    """Настройки бота из переменных окружения."""

    token: str
    admin_ids: tuple[int, ...] = ()
    courier_ids: tuple[int, ...] = ()

    @classmethod
    def from_env(cls) -> "BotConfig":
        token = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TOKEN", "")
        admin_str = os.getenv("TELEGRAM_ADMIN_IDS", "")
        admin_ids = tuple(int(x.strip()) for x in admin_str.split(",") if x.strip())
        courier_str = os.getenv("TELEGRAM_COURIERS_IDS", "")
        courier_ids = tuple(int(x.strip()) for x in courier_str.split(",") if x.strip())
        return cls(token=token, admin_ids=admin_ids, courier_ids=courier_ids)
