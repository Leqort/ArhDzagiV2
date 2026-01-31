from aiogram import Router

from bot.config import BotConfig
from bot.handlers import start, orders, products, categories


def setup_handlers(router: Router, config: BotConfig) -> None:
    start.setup(router, config)
    orders.setup(router, config)
    products.setup(router, config)
    categories.setup(router, config)