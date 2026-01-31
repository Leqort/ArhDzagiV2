"""Конфигурация телеграм-бота."""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class BotConfig:
    """Настройки бота из переменных окружения."""

    token: str
    admin_ids: tuple[int, ...] = ()
    courier_ids: tuple[int, ...] = ()
    webapp_url: str = ""  # URL Mini App (index.html), для кнопки «Открыть магазин»

    @classmethod
    def from_env(cls) -> "BotConfig":
        token = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TOKEN", "")
        admin_str = os.getenv("TELEGRAM_ADMIN_IDS", "")
        admin_ids = tuple(int(x.strip()) for x in admin_str.split(",") if x.strip())
        courier_str = os.getenv("TELEGRAM_COURIERS_IDS", "")
        courier_ids = tuple(int(x.strip()) for x in courier_str.split(",") if x.strip())
        webapp_url = (os.getenv("WEBAPP_URL") or os.getenv("BASE_URL") or "").rstrip("/")
        return cls(token=token, admin_ids=admin_ids, courier_ids=courier_ids, webapp_url=webapp_url)
