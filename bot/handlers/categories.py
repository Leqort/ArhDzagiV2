"""Обработчики управления категориями: добавление, удаление, редактирование."""
import os
import uuid

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession

from config import UPLOAD_DIR
from bot.config import BotConfig
from bot.keyboards.reply import (
    get_admin_main_keyboard,
    get_manage_categories_keyboard,
    BTN_BACK_TO_ADMIN_FROM_CATEGORIES,
)
from bot.keyboards.inline import (
    inline_delete_category_keyboard,
    inline_confirm_delete_category_keyboard,
    inline_edit_category_start_keyboard,
    inline_edit_category_fields_keyboard,
    inline_edit_category_cancel_keyboard,
    CBD_CATEGORY_DELETE_PREFIX,
    CBD_CATEGORY_DELETE_CANCEL,
    CBD_CATEGORY_DELETE_CONFIRM_PREFIX,
    CBD_CATEGORY_EDIT_PREFIX,
    CBD_CATEGORY_EDIT_CANCEL,
    CBD_CATEGORY_EDIT_FIELD_NAME,
    CBD_CATEGORY_EDIT_FIELD_IMAGE,
)
from bot.filters import AdminFilter
from bot.services.categories import CategoryService

router = Router(name="categories")


class CategoryAddStates(StatesGroup):
    waiting_name = State()
    waiting_photo = State()


class CategoryEditStates(StatesGroup):
    choosing_category = State()
    choosing_field = State()
    waiting_name = State()
    waiting_photo = State()


def setup(router_instance: Router, config: BotConfig) -> None:
    admin_filter = AdminFilter(config)

    router_instance.message.register(
        handle_manage_categories_enter,
        F.text == BTN_BACK_TO_ADMIN_FROM_CATEGORIES,
        admin_filter,
    )
    router_instance.message.register(
        handle_category_add_start,
        F.text == "➕ Добавить категорию",
        admin_filter,
    )
    router_instance.message.register(
        handle_category_delete_start,
        F.text == "🗑 Удалить категорию",
        admin_filter,
    )
    router_instance.message.register(
        handle_category_edit_start,
        F.text == "✏️ Редактировать категорию",
        admin_filter,
    )
    router_instance.message.register(
        handle_category_add_name,
        admin_filter,
        CategoryAddStates.waiting_name,
    )
    router_instance.message.register(
        handle_category_add_photo,
        admin_filter,
        CategoryAddStates.waiting_photo,
    )
    router_instance.message.register(
        handle_category_edit_name,
        admin_filter,
        CategoryEditStates.waiting_name,
    )
    router_instance.message.register(
        handle_category_edit_photo,
        admin_filter,
        CategoryEditStates.waiting_photo,
    )

    router_instance.callback_query.register(
        handle_category_delete_choice,
        F.data.startswith(CBD_CATEGORY_DELETE_PREFIX),
        admin_filter,
    )
    router_instance.callback_query.register(
        handle_category_delete_confirm,
        F.data.startswith(CBD_CATEGORY_DELETE_CONFIRM_PREFIX),
        admin_filter,
    )
    router_instance.callback_query.register(
        handle_category_delete_cancel,
        F.data == CBD_CATEGORY_DELETE_CANCEL,
        admin_filter,
    )
    router_instance.callback_query.register(
        handle_category_edit_choice,
        F.data.startswith(CBD_CATEGORY_EDIT_PREFIX),
        admin_filter,
    )
    router_instance.callback_query.register(
        handle_category_edit_cancel,
        F.data == CBD_CATEGORY_EDIT_CANCEL,
        admin_filter,
    )
    router_instance.callback_query.register(
        handle_category_edit_field_callback,
        F.data.in_({CBD_CATEGORY_EDIT_FIELD_NAME, CBD_CATEGORY_EDIT_FIELD_IMAGE}),
        admin_filter,
    )


async def handle_manage_categories_enter(message: Message, state: FSMContext) -> None:
    """Возврат в главное меню из управления категориями."""
    await state.clear()
    await message.answer(
        "Главное меню.",
        reply_markup=get_admin_main_keyboard(),
    )


# --- Вход в подменю «Управление категориями» из start.py ---
async def show_manage_categories(message: Message) -> None:
    """Показать подменю управления категориями (вызывается из start при нажатии кнопки)."""
    await message.answer(
        "Выберите действие:",
        reply_markup=get_manage_categories_keyboard(),
    )


# --- Добавление категории ---
async def handle_category_add_start(message: Message, state: FSMContext) -> None:
    await state.set_state(CategoryAddStates.waiting_name)
    await state.set_data({})
    await message.answer("Введите название категории:")


async def handle_category_add_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer("Название не может быть пустым.")
        return
    await state.update_data(name=name)
    await state.set_state(CategoryAddStates.waiting_photo)
    await message.answer("Отправьте картинку категории:")


async def handle_category_add_photo(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    if not message.photo:
        await message.answer("Отправьте именно картинку (фото).")
        return
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    ext = os.path.splitext(file.file_path or ".jpg")[1] or ".jpg"
    filename = f"{uuid.uuid4()}{ext}"
    path = os.path.join(UPLOAD_DIR, filename)
    await message.bot.download_file(file.file_path, path)
    data = await state.get_data()
    name = data["name"]
    service = CategoryService(session)
    category = await service.create_category(name, filename)
    await state.clear()
    await message.answer(
        f"Категория «{category.name}» создана (ID: {category.id}).",
        reply_markup=get_manage_categories_keyboard(),
    )


# --- Удаление категории ---
async def handle_category_delete_start(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    await state.clear()
    service = CategoryService(session)
    categories = await service.get_categories()
    if not categories:
        await message.answer(
            "Нет категорий для удаления.",
            reply_markup=get_manage_categories_keyboard(),
        )
        return
    await message.answer(
        "Выберите категорию для удаления:",
        reply_markup=inline_delete_category_keyboard([(c.id, c.name) for c in categories]),
    )


async def handle_category_delete_choice(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    try:
        await callback.answer()
    except TelegramBadRequest:
        pass
    category_id = int(callback.data.removeprefix(CBD_CATEGORY_DELETE_PREFIX))
    service = CategoryService(session)
    category = await service.get_category(category_id)
    if not category:
        await callback.message.answer("Категория не найдена.")
        return
    await callback.message.answer(
        f"Удалить категорию «{category.name}» (ID: {category_id})?",
        reply_markup=inline_confirm_delete_category_keyboard(category_id),
    )


async def handle_category_delete_confirm(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    try:
        await callback.answer()
    except TelegramBadRequest:
        pass
    category_id = int(callback.data.removeprefix(CBD_CATEGORY_DELETE_CONFIRM_PREFIX))
    service = CategoryService(session)
    ok = await service.delete_category(category_id)
    await state.clear()
    if ok:
        await callback.message.answer(
            f"Категория (ID: {category_id}) удалена.",
            reply_markup=get_manage_categories_keyboard(),
        )
    else:
        await callback.message.answer("Категория не найдена.")


async def handle_category_delete_cancel(
    callback: CallbackQuery, state: FSMContext
) -> None:
    try:
        await callback.answer()
    except TelegramBadRequest:
        pass
    await state.clear()
    await callback.message.answer(
        "Удаление отменено.",
        reply_markup=get_manage_categories_keyboard(),
    )


# --- Редактирование категории ---
async def handle_category_edit_start(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    await state.clear()
    service = CategoryService(session)
    categories = await service.get_categories()
    if not categories:
        await message.answer(
            "Нет категорий для редактирования.",
            reply_markup=get_manage_categories_keyboard(),
        )
        return
    await message.answer(
        "Выберите категорию для редактирования:",
        reply_markup=inline_edit_category_start_keyboard([(c.id, c.name) for c in categories]),
    )


async def handle_category_edit_choice(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    try:
        await callback.answer()
    except TelegramBadRequest:
        pass
    category_id = int(callback.data.removeprefix(CBD_CATEGORY_EDIT_PREFIX))
    service = CategoryService(session)
    category = await service.get_category(category_id)
    if not category:
        await callback.message.answer("Категория не найдена.")
        return
    await state.update_data(category_id=category_id)
    await state.set_state(CategoryEditStates.choosing_field)
    await callback.message.answer(
        f"Категория: «{category.name}». Что изменить?",
        reply_markup=inline_edit_category_fields_keyboard(),
    )


async def handle_category_edit_field_callback(
    callback: CallbackQuery, state: FSMContext
) -> None:
    try:
        await callback.answer()
    except TelegramBadRequest:
        pass
    data = callback.data
    if data == CBD_CATEGORY_EDIT_FIELD_NAME:
        await state.set_state(CategoryEditStates.waiting_name)
        await callback.message.answer(
            "Введите новое название категории:",
            reply_markup=inline_edit_category_cancel_keyboard(),
        )
    elif data == CBD_CATEGORY_EDIT_FIELD_IMAGE:
        await state.set_state(CategoryEditStates.waiting_photo)
        await callback.message.answer(
            "Отправьте новую картинку категории:",
            reply_markup=inline_edit_category_cancel_keyboard(),
        )


async def handle_category_edit_name(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer("Название не может быть пустым.")
        return
    data = await state.get_data()
    category_id = data.get("category_id")
    if not category_id:
        await message.answer("Ошибка: категория не выбрана.")
        return
    service = CategoryService(session)
    ok = await service.update_category_name(category_id, name)
    await state.clear()
    if ok:
        await message.answer(
            f"Название категории изменено на «{name}».",
            reply_markup=get_manage_categories_keyboard(),
        )
    else:
        await message.answer("Категория не найдена.")


async def handle_category_edit_photo(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    if not message.photo:
        await message.answer("Отправьте именно картинку.")
        return
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    ext = os.path.splitext(file.file_path or ".jpg")[1] or ".jpg"
    filename = f"{uuid.uuid4()}{ext}"
    path = os.path.join(UPLOAD_DIR, filename)
    await message.bot.download_file(file.file_path, path)
    data = await state.get_data()
    category_id = data.get("category_id")
    if not category_id:
        await message.answer("Ошибка: категория не выбрана.")
        return
    service = CategoryService(session)
    ok = await service.update_category_photo(category_id, filename)
    await state.clear()
    if ok:
        await message.answer(
            "Картинка категории обновлена.",
            reply_markup=get_manage_categories_keyboard(),
        )
    else:
        await message.answer("Категория не найдена.")


async def handle_category_edit_cancel(
    callback: CallbackQuery, state: FSMContext
) -> None:
    try:
        await callback.answer()
    except TelegramBadRequest:
        pass
    await state.clear()
    await callback.message.answer(
        "Редактирование отменено.",
        reply_markup=get_manage_categories_keyboard(),
    )
