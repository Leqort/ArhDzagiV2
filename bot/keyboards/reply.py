"""Reply-клавиатуры."""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


# Тексты кнопок для админов
BTN_ADMIN_PRODUCTS = "📦 Управление товарами"
BTN_ADMIN_CATEGORIES = "📂 Управление категориями"
BTN_ADMIN_ORDERS = "📋 Управление заказами"
BTN_ORDERS_NEW = "🆕 Новые заказы"
BTN_ORDERS_ACTIVE = "🔄 Активные заказы"
BTN_ORDERS_COMPLETED = "✅ Завершённые заказы"
BTN_ORDERS_CANCELLED = "❌ Отменённые заказы"
BTN_PRODUCT_ADD = "➕ Добавление товаров"
BTN_PRODUCT_DELETE = "🗑 Удаление товаров"
BTN_PRODUCT_EDIT = "✏️ Редактирование товаров"
BTN_BACK_TO_ADMIN = "◀️ В главное меню"
# Редактирование товара — что изменить (по одному)
BTN_EDIT_NAME = "📝 Название"
BTN_EDIT_DESCRIPTION = "📄 Описание"
BTN_EDIT_IMAGE = "🖼 Картинка"
BTN_EDIT_FLAVORS = "🍬 Вкусы"
BTN_BACK_TO_MANAGE_PRODUCTS = "◀️ К управлению товарами"
# Вкусы товара (под сообщением)
BTN_ADD_FLAVOR = "🍬 Добавить вкус"
BTN_FLAVORS_DONE = "✅ Готово"
BTN_FLAVORS_BACK = "◀️ Назад"


def get_admin_main_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню для администратора."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=BTN_ADMIN_PRODUCTS),
                KeyboardButton(text=BTN_ADMIN_CATEGORIES),
            ],
            [KeyboardButton(text=BTN_ADMIN_ORDERS)],
        ],
        resize_keyboard=True,
    )


def get_courier_main_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню для курьера (только просмотр заказов)."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=BTN_ORDERS_NEW),
                KeyboardButton(text=BTN_ORDERS_ACTIVE),
            ],
            [
                KeyboardButton(text=BTN_ORDERS_COMPLETED),
                KeyboardButton(text=BTN_ORDERS_CANCELLED),
            ],
        ],
        resize_keyboard=True,
    )


def get_manage_products_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура подменю «Управление товарами»."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=BTN_PRODUCT_ADD),
                KeyboardButton(text=BTN_PRODUCT_DELETE),
                KeyboardButton(text=BTN_PRODUCT_EDIT),
            ],
            [KeyboardButton(text=BTN_BACK_TO_ADMIN)],
        ],
        resize_keyboard=True,
    )


def get_manage_orders_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура подменю «Управление заказами» (только просмотр заказов)."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=BTN_ORDERS_NEW),
                KeyboardButton(text=BTN_ORDERS_ACTIVE),
            ],
            [
                KeyboardButton(text=BTN_ORDERS_COMPLETED),
                KeyboardButton(text=BTN_ORDERS_CANCELLED),
            ],
            [KeyboardButton(text=BTN_BACK_TO_ADMIN)],
        ],
        resize_keyboard=True,
    )


def get_edit_product_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура выбора поля при редактировании товара (по одному)."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_EDIT_NAME), KeyboardButton(text=BTN_EDIT_DESCRIPTION)],
            [KeyboardButton(text=BTN_EDIT_IMAGE), KeyboardButton(text=BTN_EDIT_FLAVORS)],
            [KeyboardButton(text=BTN_BACK_TO_MANAGE_PRODUCTS)],
        ],
        resize_keyboard=True,
    )


def get_product_flavors_keyboard_add(flavors: list, selected_ids: set | None = None) -> ReplyKeyboardMarkup:
    """Клавиатура выбора вкусов при добавлении товара: все вкусы + «Добавить вкус» + «Готово».
    flavors — список Flavor (id, name); selected_ids — множество выбранных id (для пометки опционально).
    """
    rows = []
    for f in flavors:
        rows.append([KeyboardButton(text=f.name)])
    rows.append([KeyboardButton(text=BTN_ADD_FLAVOR)])
    rows.append([KeyboardButton(text=BTN_FLAVORS_DONE)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def get_product_flavors_keyboard_edit(flavors: list) -> ReplyKeyboardMarkup:
    """Клавиатура вкусов товара при редактировании: вкусы товара + «Добавить вкус» + «Назад».
    flavors — список Flavor (id, name) у данного товара.
    """
    rows = []
    for f in flavors:
        rows.append([KeyboardButton(text=f.name)])
    rows.append([KeyboardButton(text=BTN_ADD_FLAVOR)])
    rows.append([KeyboardButton(text=BTN_FLAVORS_BACK)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
