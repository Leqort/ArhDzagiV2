"""Обработчики заказов: просмотр по статусам и подменю управления (для админов и курьеров)."""
from aiogram import Router, F
from aiogram.types import Message

from bot.config import BotConfig
from bot.keyboards.reply import (
    get_manage_orders_keyboard,
    get_admin_main_keyboard,
    BTN_ADMIN_ORDERS,
    BTN_ORDERS_NEW,
    BTN_ORDERS_ACTIVE,
    BTN_ORDERS_COMPLETED,
    BTN_ORDERS_CANCELLED,
    BTN_BACK_TO_ADMIN,
)
from bot.filters import AdminFilter, StaffFilter

router = Router(name="orders")


def setup(router_instance: Router, config: BotConfig) -> None:
    """Регистрирует хендлеры заказов (подменю + просмотр по статусам)."""
    admin_filter = AdminFilter(config)
    staff_filter = StaffFilter(config)

    router_instance.message.register(
        handle_manage_orders, F.text == BTN_ADMIN_ORDERS, admin_filter
    )
    router_instance.message.register(
        handle_back_to_admin, F.text == BTN_BACK_TO_ADMIN, admin_filter
    )
    router_instance.message.register(
        handle_orders_new, F.text == BTN_ORDERS_NEW, staff_filter
    )
    router_instance.message.register(
        handle_orders_active, F.text == BTN_ORDERS_ACTIVE, staff_filter
    )
    router_instance.message.register(
        handle_orders_completed, F.text == BTN_ORDERS_COMPLETED, staff_filter
    )
    router_instance.message.register(
        handle_orders_cancelled, F.text == BTN_ORDERS_CANCELLED, staff_filter
    )


async def handle_manage_orders(message: Message) -> None:
    """Подменю «Управление заказами»: просмотр заказов + добавление/удаление/редактирование товаров."""
    await message.answer(
        "Выберите действие:",
        reply_markup=get_manage_orders_keyboard(),
    )


async def handle_back_to_admin(message: Message) -> None:
    """Возврат в главное меню администратора."""
    await message.answer(
        "Главное меню.",
        reply_markup=get_admin_main_keyboard(),
    )


async def handle_orders_new(message: Message) -> None:
    """Просмотр новых заказов."""
    await message.answer("Список новых заказов пока пуст.")


async def handle_orders_active(message: Message) -> None:
    """Просмотр активных заказов."""
    await message.answer("Список активных заказов пока пуст.")


async def handle_orders_completed(message: Message) -> None:
    """Просмотр завершённых заказов."""
    await message.answer("Список завершённых заказов пока пуст.")


async def handle_orders_cancelled(message: Message) -> None:
    """Просмотр отменённых заказов."""
    await message.answer("Список отменённых заказов пока пуст.")
