"""Обработчик /start и главное меню по ролям (админ, курьер, пользователь)."""
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart

from bot.config import BotConfig
from bot.keyboards.reply import (
    get_admin_main_keyboard,
    get_courier_main_keyboard,
    get_manage_products_keyboard,
    get_manage_categories_keyboard,
    BTN_ADMIN_PRODUCTS,
    BTN_ADMIN_CATEGORIES,
)
from bot.filters import AdminFilter

router = Router(name="start")

# Сообщение о ArhDzagi для обычных пользователей
WELCOME_USER = (
    "👋 Добро пожаловать в ArhDzagi!\n\n"
    "ArhDzagi — это ваш надёжный магазин. "
    "Здесь вы можете ознакомиться с ассортиментом и оформить заказ.\n\n"
    "Используйте меню бота или напишите нам, если нужна помощь."
)


def setup(router_instance: Router, config: BotConfig) -> None:
    """Регистрирует хендлеры start с учётом конфига (роли)."""
    admin_filter = AdminFilter(config)

    async def start_handler(message: Message) -> None:
        await cmd_start(message, config)

    router_instance.message.register(start_handler, CommandStart())
    router_instance.message.register(
        handle_manage_products, F.text == BTN_ADMIN_PRODUCTS, admin_filter
    )
    router_instance.message.register(
        handle_manage_categories, F.text == BTN_ADMIN_CATEGORIES, admin_filter
    )


async def cmd_start(message: Message, config: BotConfig) -> None:
    """Приветствие и меню в зависимости от роли."""
    user_id = message.from_user.id if message.from_user else 0
    if user_id in config.admin_ids:
        await message.answer(
            "👋 Добро пожаловать в панель администратора.\n\n"
            "Выберите действие в меню ниже.",
            reply_markup=get_admin_main_keyboard(),
        )
    elif user_id in config.courier_ids:
        await message.answer(
            "👋 Добро пожаловать, курьер.\n\n"
            "Ниже — разделы для просмотра заказов.",
            reply_markup=get_courier_main_keyboard(),
        )
    else:
        await message.answer(WELCOME_USER)


async def handle_manage_products(message: Message) -> None:
    """Подменю «Управление товарами»: добавление/удаление/редактирование."""
    await message.answer(
        "Выберите действие:",
        reply_markup=get_manage_products_keyboard(),
    )


async def handle_manage_categories(message: Message) -> None:
    """Подменю «Управление категориями»: добавить / удалить / редактировать."""
    await message.answer(
        "Выберите действие:",
        reply_markup=get_manage_categories_keyboard(),
    )
