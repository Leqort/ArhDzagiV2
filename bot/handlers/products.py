"""Обработчики товаров: добавление, удаление, редактирование (используют бэкенд/БД)."""
import os
import uuid

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from config import UPLOAD_DIR
from bot.config import BotConfig
from bot.keyboards.reply import (
    get_manage_products_keyboard,
    BTN_PRODUCT_ADD,
    BTN_PRODUCT_DELETE,
    BTN_PRODUCT_EDIT,
    BTN_BACK_TO_MANAGE_PRODUCTS,
    BTN_EDIT_NAME,
    BTN_EDIT_DESCRIPTION,
    BTN_EDIT_IMAGE,
    BTN_EDIT_FLAVORS,
)
from bot.keyboards.inline import (
    inline_delete_product_keyboard,
    inline_edit_product_start_keyboard,
    inline_edit_product_fields_keyboard,
    inline_edit_cancel_keyboard,
    inline_edit_flavor_keyboard,
    inline_flavors_keyboard_add,
    inline_flavors_keyboard_edit,
    CBD_PRODUCT_DELETE_CANCEL,
    CBD_PRODUCT_DELETE_CONFIRM_PREFIX,
    CBD_PRODUCT_EDIT_CANCEL,
    CBD_PRODUCT_DELETE_PREFIX,
    inline_confirm_delete_product_keyboard,
    CBD_PRODUCT_EDIT_PREFIX,
    CBD_EDIT_NAME,
    CBD_EDIT_DESCRIPTION,
    CBD_EDIT_IMAGE,
    CBD_EDIT_FLAVORS,
    CBD_FLAVOR_EDIT_NAME_PREFIX,
    CBD_FLAVOR_EDIT_PHOTO_PREFIX,
    CBD_FLAVOR_EDIT_BACK,
    CBD_ADD_FLAVOR_SELECT_PREFIX,
    CBD_ADD_FLAVOR_NEW,
    CBD_ADD_FLAVOR_DONE,
    CBD_PRODUCT_EDIT_FLAVOR_PREFIX,
    CBD_EDIT_FLAVOR_ADD_PREFIX,
    CBD_PRODUCT_EDIT_FLAVORS_BACK,
)
from bot.filters import AdminFilter
from bot.services.items import ItemService

router = Router(name="products")


class ProductEditStates(StatesGroup):
    """Состояния FSM при редактировании товара (по одному полю)."""
    waiting_product_id = State()
    choosing_field = State()
    choosing_flavor = State()  # список вкусов товара + кнопки
    waiting_name = State()
    waiting_description = State()
    waiting_image = State()
    waiting_flavors = State()  # текст: ввод названия вкуса (старый сценарий — не используется при выборе из клавиатуры)
    waiting_flavor_name = State()   # новое название вкуса
    waiting_flavor_photo = State()  # новое фото вкуса
    waiting_new_flavor_name = State()
    waiting_new_flavor_photo = State()


class ProductAddStates(StatesGroup):
    """Состояния FSM при добавлении товара."""
    waiting_name = State()
    waiting_description = State()
    waiting_price = State()
    waiting_photo = State()
    waiting_flavors = State()  # выбор вкусов из клавиатуры (кнопки + Добавить вкус + Готово)
    waiting_new_flavor_name = State()
    waiting_new_flavor_photo = State()


def setup(router_instance: Router, config: BotConfig) -> None:
    """Регистрирует хендлеры товаров (только админ)."""
    admin_filter = AdminFilter(config)

    router_instance.message.register(
        handle_product_add, F.text == BTN_PRODUCT_ADD, admin_filter
    )
    router_instance.message.register(
        handle_product_delete_start, F.text == BTN_PRODUCT_DELETE, admin_filter
    )
    router_instance.message.register(
        handle_product_edit_start, F.text == BTN_PRODUCT_EDIT, admin_filter
    )
    router_instance.message.register(
        handle_back_to_manage_products,
        F.text == BTN_BACK_TO_MANAGE_PRODUCTS,
        admin_filter,
    )

    # Callback: выбор товара для удаления (подтверждение) и подтверждение удаления
    router_instance.callback_query.register(
        handle_product_delete_confirm,
        F.data.startswith(CBD_PRODUCT_DELETE_CONFIRM_PREFIX),
        admin_filter,
    )
    router_instance.callback_query.register(
        handle_product_delete_choice,
        F.data.startswith(CBD_PRODUCT_DELETE_PREFIX),
        admin_filter,
    )
    router_instance.callback_query.register(
        handle_product_edit_choice,
        F.data.startswith(CBD_PRODUCT_EDIT_PREFIX),
        admin_filter,
    )
    # Редактирование: выбор поля
    router_instance.message.register(
        handle_edit_field_name,
        F.text == BTN_EDIT_NAME,
        admin_filter,
        ProductEditStates.choosing_field,
    )
    router_instance.message.register(
        handle_edit_field_description,
        F.text == BTN_EDIT_DESCRIPTION,
        admin_filter,
        ProductEditStates.choosing_field,
    )
    router_instance.message.register(
        handle_edit_field_image,
        F.text == BTN_EDIT_IMAGE,
        admin_filter,
        ProductEditStates.choosing_field,
    )
    router_instance.message.register(
        handle_edit_field_flavors,
        F.text == BTN_EDIT_FLAVORS,
        admin_filter,
        ProductEditStates.choosing_field,
    )
    router_instance.message.register(
        handle_edit_new_flavor_name,
        admin_filter,
        ProductEditStates.waiting_new_flavor_name,
    )
    router_instance.message.register(
        handle_edit_new_flavor_photo,
        admin_filter,
        ProductEditStates.waiting_new_flavor_photo,
    )
    router_instance.message.register(
        handle_edit_flavor_name_receive,
        admin_filter,
        ProductEditStates.waiting_flavor_name,
    )
    router_instance.message.register(
        handle_edit_flavor_photo_receive,
        admin_filter,
        ProductEditStates.waiting_flavor_photo,
    )
    router_instance.message.register(
        handle_receive_name, admin_filter, ProductEditStates.waiting_name
    )
    router_instance.message.register(
        handle_receive_description, admin_filter, ProductEditStates.waiting_description
    )
    router_instance.message.register(
        handle_receive_image, admin_filter, ProductEditStates.waiting_image
    )
    router_instance.message.register(
        handle_receive_flavors, admin_filter, ProductEditStates.waiting_flavors
    )

    # Добавление товара: по шагам
    router_instance.message.register(
        handle_add_name, admin_filter, ProductAddStates.waiting_name
    )
    router_instance.message.register(
        handle_add_description, admin_filter, ProductAddStates.waiting_description
    )
    router_instance.message.register(
        handle_add_price, admin_filter, ProductAddStates.waiting_price
    )
    router_instance.message.register(
        handle_add_photo, admin_filter, ProductAddStates.waiting_photo
    )
    router_instance.message.register(
        handle_add_new_flavor_name, admin_filter, ProductAddStates.waiting_new_flavor_name
    )
    router_instance.message.register(
        handle_add_new_flavor_photo, admin_filter, ProductAddStates.waiting_new_flavor_photo
    )

    # Callback: отмена удаления / редактирования и выбор поля редактирования
    router_instance.callback_query.register(
        handle_product_delete_cancel, F.data == CBD_PRODUCT_DELETE_CANCEL, admin_filter
    )
    router_instance.callback_query.register(
        handle_product_edit_cancel, F.data == CBD_PRODUCT_EDIT_CANCEL, admin_filter
    )
    router_instance.callback_query.register(
        handle_product_edit_field_callback,
        F.data.in_({CBD_EDIT_NAME, CBD_EDIT_DESCRIPTION, CBD_EDIT_IMAGE, CBD_EDIT_FLAVORS}),
        admin_filter,
    )
    # Callback: редактирование вкуса (название, фото, назад)
    router_instance.callback_query.register(
        handle_flavor_edit_name_callback,
        F.data.startswith(CBD_FLAVOR_EDIT_NAME_PREFIX),
        admin_filter,
    )
    router_instance.callback_query.register(
        handle_flavor_edit_photo_callback,
        F.data.startswith(CBD_FLAVOR_EDIT_PHOTO_PREFIX),
        admin_filter,
    )
    router_instance.callback_query.register(
        handle_flavor_edit_back_callback,
        F.data == CBD_FLAVOR_EDIT_BACK,
        admin_filter,
    )
    # Callback: вкусы при добавлении товара (инлайн под сообщением)
    router_instance.callback_query.register(
        handle_add_flavor_select,
        F.data.startswith(CBD_ADD_FLAVOR_SELECT_PREFIX),
        admin_filter,
    )
    router_instance.callback_query.register(
        handle_add_flavor_new_callback,
        F.data == CBD_ADD_FLAVOR_NEW,
        admin_filter,
    )
    router_instance.callback_query.register(
        handle_add_flavor_done_callback,
        F.data == CBD_ADD_FLAVOR_DONE,
        admin_filter,
    )
    # Callback: вкусы при редактировании товара (инлайн под сообщением)
    router_instance.callback_query.register(
        handle_product_edit_flavor_callback,
        F.data.startswith(CBD_PRODUCT_EDIT_FLAVOR_PREFIX),
        admin_filter,
    )
    router_instance.callback_query.register(
        handle_edit_flavor_add_callback,
        F.data.startswith(CBD_EDIT_FLAVOR_ADD_PREFIX),
        admin_filter,
    )
    router_instance.callback_query.register(
        handle_product_edit_flavors_back_callback,
        F.data == CBD_PRODUCT_EDIT_FLAVORS_BACK,
        admin_filter,
    )


# --- Callback: отмена и выбор поля (клавиатура к сообщению) ---


async def handle_product_delete_cancel(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Отмена удаления — возврат в подменю товаров."""
    try:
        await callback.answer()
    except TelegramBadRequest:
        pass
    await state.clear()
    await callback.message.answer(
        "Управление товарами.",
        reply_markup=get_manage_products_keyboard(),
    )


async def handle_product_edit_cancel(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Отмена редактирования — возврат в подменю товаров."""
    try:
        await callback.answer()
    except TelegramBadRequest:
        pass
    await state.clear()
    await callback.message.answer(
        "Управление товарами.",
        reply_markup=get_manage_products_keyboard(),
    )


async def handle_product_edit_field_callback(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    """Выбор поля редактирования по inline-кнопке (название/описание/картинка/вкусы)."""
    try:
        await callback.answer()
    except TelegramBadRequest:
        pass
    data = callback.data
    if data == CBD_EDIT_NAME:
        await state.set_state(ProductEditStates.waiting_name)
        await callback.message.answer(
            "Введите новое название товара:",
            reply_markup=inline_edit_cancel_keyboard(),
        )
    elif data == CBD_EDIT_DESCRIPTION:
        await state.set_state(ProductEditStates.waiting_description)
        await callback.message.answer(
            "Введите новое описание товара:",
            reply_markup=inline_edit_cancel_keyboard(),
        )
    elif data == CBD_EDIT_IMAGE:
        await state.set_state(ProductEditStates.waiting_image)
        await callback.message.answer(
            "Отправьте новое фото товара:",
            reply_markup=inline_edit_cancel_keyboard(),
        )
    elif data == CBD_EDIT_FLAVORS:
        await state.set_state(ProductEditStates.choosing_flavor)
        sdata = await state.get_data()
        product_id = sdata.get("product_id")
        if not product_id:
            await callback.message.answer("Ошибка: товар не выбран.")
            return
        service = ItemService(session)
        item = await service.get_item(product_id)
        if not item:
            await callback.message.answer("Товар не найден.")
            return
        names = ", ".join(f.name for f in item.flavors) if item.flavors else "пока нет"
        await callback.message.answer(
            f"Вкусы товара: {names}. Выберите вкус для редактирования или нажмите «Добавить вкус».",
            reply_markup=inline_flavors_keyboard_edit(item.flavors, product_id),
        )


# --- Назад к подменю товаров ---


async def handle_back_to_manage_products(message: Message, state: FSMContext) -> None:
    """Возврат к подменю «Управление товарами»."""
    await state.clear()
    await message.answer(
        "Управление товарами.",
        reply_markup=get_manage_products_keyboard(),
    )


# --- Добавление товара ---


async def handle_product_add(message: Message, state: FSMContext) -> None:
    """Старт добавления товара: запрос названия."""
    await state.set_state(ProductAddStates.waiting_name)
    await state.set_data({})
    await message.answer("Введите название товара:")


async def handle_add_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer("Название не может быть пустым.")
        return
    await state.update_data(name=name)
    await state.set_state(ProductAddStates.waiting_description)
    await message.answer("Введите описание товара:")


async def handle_add_description(message: Message, state: FSMContext) -> None:
    description = (message.text or "").strip()
    await state.update_data(description=description)
    await state.set_state(ProductAddStates.waiting_price)
    await message.answer("Введите цену товара (число):")


async def handle_add_price(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip().replace(",", ".")
    try:
        price = float(text)
        if price < 0:
            raise ValueError("negative")
    except ValueError:
        await message.answer("Введите число (например: 299 или 99.50).")
        return
    await state.update_data(price=price)
    await state.set_state(ProductAddStates.waiting_photo)
    await message.answer("Отправьте фото товара:")


async def handle_add_photo(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    if not message.photo:
        await message.answer("Отправьте именно фото (картинку).")
        return
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    ext = os.path.splitext(file.file_path or ".jpg")[1] or ".jpg"
    filename = f"{uuid.uuid4()}{ext}"
    path = os.path.join(UPLOAD_DIR, filename)
    await message.bot.download_file(file.file_path, path)
    await state.update_data(photo_filename=filename, selected_flavor_ids=[])
    await state.set_state(ProductAddStates.waiting_flavors)
    service = ItemService(session)
    flavors = await service.get_flavors_by_ids([])
    sent = await message.answer(
        "Вкусы товара. Добавьте свои вкусы кнопкой ниже или нажмите «Готово»:",
        reply_markup=inline_flavors_keyboard_add(flavors, set()),
    )
    await state.update_data(
        flavor_keyboard_chat_id=sent.chat.id,
        flavor_keyboard_message_id=sent.message_id,
    )


async def handle_add_flavor_select(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    """Выбор/снятие вкуса при добавлении товара (инлайн под сообщением). Вкусы уникальны в списке."""
    try:
        await callback.answer()
    except TelegramBadRequest:
        pass
    flavor_id = int(callback.data.removeprefix(CBD_ADD_FLAVOR_SELECT_PREFIX))
    data = await state.get_data()
    selected_ids: set[int] = set(data.get("selected_flavor_ids") or [])
    if flavor_id in selected_ids:
        selected_ids.discard(flavor_id)
    else:
        selected_ids.add(flavor_id)
    await state.update_data(selected_flavor_ids=list(selected_ids))
    service = ItemService(session)
    flavors = await service.get_flavors_by_ids(list(selected_ids))
    try:
        await callback.message.edit_reply_markup(
            reply_markup=inline_flavors_keyboard_add(flavors, selected_ids),
        )
    except TelegramBadRequest:
        pass


async def handle_add_flavor_new_callback(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Кнопка «Добавить вкус» при добавлении товара."""
    try:
        await callback.answer()
    except TelegramBadRequest:
        pass
    await state.set_state(ProductAddStates.waiting_new_flavor_name)
    await callback.message.answer("Введите название нового вкуса:")


async def handle_add_flavor_done_callback(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    """Кнопка «Готово» при добавлении товара — создаём товар с выбранными вкусами."""
    try:
        await callback.answer()
    except TelegramBadRequest:
        pass
    data = await state.get_data()
    selected_ids: list[int] = list(data.get("selected_flavor_ids") or [])
    name = data["name"]
    description = data["description"]
    price = data["price"]
    photo_filename = data["photo_filename"]
    service = ItemService(session)
    try:
        item = await service.create_item(
            name=name,
            description=description,
            price=price,
            photo_filename=photo_filename,
            flavor_ids=selected_ids if selected_ids else None,
        )
        await state.clear()
        await callback.message.answer(
            f"Товар «{item.name}» создан (ID: {item.id}).",
            reply_markup=get_manage_products_keyboard(),
        )
    except Exception as e:
        await callback.message.answer(f"Ошибка при создании: {e}")


async def handle_add_new_flavor_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer("Название не может быть пустым.")
        return
    await state.update_data(new_flavor_name=name)
    await state.set_state(ProductAddStates.waiting_new_flavor_photo)
    await message.answer("Отправьте фото вкуса:")


async def handle_add_new_flavor_photo(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    if not message.photo:
        await message.answer("Отправьте именно фото.")
        return
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    ext = os.path.splitext(file.file_path or ".jpg")[1] or ".jpg"
    filename = f"{uuid.uuid4()}{ext}"
    path = os.path.join(UPLOAD_DIR, filename)
    await message.bot.download_file(file.file_path, path)
    data = await state.get_data()
    name = data["new_flavor_name"]
    service = ItemService(session)
    flavor = await service.create_flavor(name, filename)
    selected_ids: list[int] = list(data.get("selected_flavor_ids") or [])
    if flavor.id not in selected_ids:
        selected_ids.append(flavor.id)
    await state.update_data(selected_flavor_ids=selected_ids)
    await state.set_state(ProductAddStates.waiting_flavors)
    flavors = await service.get_flavors_by_ids(selected_ids)
    selected_set = set(selected_ids)
    text = (
        "Вкус «{0}» создан и добавлен. Вкусы товара — выберите кнопками под сообщением или нажмите «Готово»."
    ).format(flavor.name)
    chat_id = data.get("flavor_keyboard_chat_id")
    msg_id = data.get("flavor_keyboard_message_id")
    if chat_id is not None and msg_id is not None:
        try:
            await message.bot.edit_message_text(
                chat_id=chat_id,
                message_id=msg_id,
                text=text,
                reply_markup=inline_flavors_keyboard_add(flavors, selected_set),
            )
        except Exception:
            await message.answer(
                text,
                reply_markup=inline_flavors_keyboard_add(flavors, selected_set),
            )
    else:
        await message.answer(
            text,
            reply_markup=inline_flavors_keyboard_add(flavors, selected_set),
        )


# --- Удаление товара ---


async def handle_product_delete_start(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    """Старт удаления: показать список товаров для выбора."""
    await state.clear()
    service = ItemService(session)
    items = await service.get_items()
    if not items:
        await message.answer(
            "Нет товаров для удаления.",
            reply_markup=get_manage_products_keyboard(),
        )
        return
    await message.answer(
        "Выберите товар для удаления:",
        reply_markup=inline_delete_product_keyboard([(i.id, i.name) for i in items]),
    )


async def handle_product_delete_choice(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    """Выбор товара для удаления: показываем подтверждение."""
    try:
        await callback.answer()
    except TelegramBadRequest:
        pass
    item_id = int(callback.data.removeprefix(CBD_PRODUCT_DELETE_PREFIX))
    service = ItemService(session)
    item = await service.get_item(item_id)
    if not item:
        await callback.message.answer("Товар не найден.")
        return
    await callback.message.answer(
        f"Удалить товар «{item.name}» (ID: {item_id})?",
        reply_markup=inline_confirm_delete_product_keyboard(item_id),
    )


async def handle_product_delete_confirm(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    """Подтверждение удаления товара по inline-кнопке «Да, удалить»."""
    try:
        await callback.answer()
    except TelegramBadRequest:
        pass
    item_id = int(callback.data.removeprefix(CBD_PRODUCT_DELETE_CONFIRM_PREFIX))
    service = ItemService(session)
    ok = await service.delete_item(item_id)
    await state.clear()
    if ok:
        await callback.message.answer(
            f"Товар (ID: {item_id}) удалён.",
            reply_markup=get_manage_products_keyboard(),
        )
    else:
        await callback.message.answer("Товар не найден.")


# --- Редактирование товара (по одному полю) ---


async def handle_product_edit_start(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    """Старт редактирования: показать список товаров для выбора."""
    await state.clear()
    service = ItemService(session)
    items = await service.get_items()
    if not items:
        await message.answer(
            "Нет товаров для редактирования.",
            reply_markup=get_manage_products_keyboard(),
        )
        return
    await message.answer(
        "Выберите товар для редактирования:",
        reply_markup=inline_edit_product_start_keyboard([(i.id, i.name) for i in items]),
    )


async def handle_product_edit_choice(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    """Выбор товара для редактирования по inline-кнопке."""
    try:
        await callback.answer()
    except TelegramBadRequest:
        pass  # запрос устарел — всё равно выполняем действие и отправим новое сообщение
    product_id = int(callback.data.removeprefix(CBD_PRODUCT_EDIT_PREFIX))
    service = ItemService(session)
    item = await service.get_item(product_id)
    if not item:
        await callback.message.answer("Товар не найден.")
        return
    await state.update_data(product_id=product_id)
    await state.set_state(ProductEditStates.choosing_field)
    await callback.message.answer(
        f"Товар: «{item.name}». Что изменить?",
        reply_markup=inline_edit_product_fields_keyboard(),
    )


async def handle_edit_field_name(message: Message, state: FSMContext) -> None:
    await state.set_state(ProductEditStates.waiting_name)
    await message.answer(
        "Введите новое название товара:",
        reply_markup=inline_edit_cancel_keyboard(),
    )


async def handle_edit_field_description(message: Message, state: FSMContext) -> None:
    await state.set_state(ProductEditStates.waiting_description)
    await message.answer(
        "Введите новое описание товара:",
        reply_markup=inline_edit_cancel_keyboard(),
    )


async def handle_edit_field_image(message: Message, state: FSMContext) -> None:
    await state.set_state(ProductEditStates.waiting_image)
    await message.answer(
        "Отправьте новое фото товара:",
        reply_markup=inline_edit_cancel_keyboard(),
    )


async def handle_edit_field_flavors(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    await state.set_state(ProductEditStates.choosing_flavor)
    data = await state.get_data()
    product_id = data.get("product_id")
    if not product_id:
        await message.answer("Ошибка: товар не выбран.")
        return
    service = ItemService(session)
    item = await service.get_item(product_id)
    if not item:
        await message.answer("Товар не найден.")
        return
    names = ", ".join(f.name for f in item.flavors) if item.flavors else "пока нет"
    await message.answer(
        f"Вкусы товара: {names}. Выберите вкус для редактирования или нажмите «Добавить вкус».",
        reply_markup=inline_flavors_keyboard_edit(item.flavors, product_id),
    )


async def handle_product_edit_flavor_callback(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    """Выбор вкуса для редактирования (название/фото) — инлайн под сообщением. Вкусы уникальны для товара."""
    try:
        await callback.answer()
    except TelegramBadRequest:
        pass
    flavor_id = int(callback.data.removeprefix(CBD_PRODUCT_EDIT_FLAVOR_PREFIX))
    service = ItemService(session)
    flavor = await service.get_flavor(flavor_id)
    if not flavor:
        await callback.message.answer("Вкус не найден.")
        return
    await callback.message.answer(
        f"Вкус: «{flavor.name}». Что изменить?",
        reply_markup=inline_edit_flavor_keyboard(flavor_id),
    )


async def handle_edit_flavor_add_callback(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Кнопка «Добавить вкус» при редактировании товара."""
    try:
        await callback.answer()
    except TelegramBadRequest:
        pass
    await state.set_state(ProductEditStates.waiting_new_flavor_name)
    await callback.message.answer("Введите название нового вкуса:")


async def handle_product_edit_flavors_back_callback(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Кнопка «Назад» из списка вкусов к выбору поля редактирования."""
    try:
        await callback.answer()
    except TelegramBadRequest:
        pass
    await state.set_state(ProductEditStates.choosing_field)
    await callback.message.answer(
        "Что изменить? (по одному полю)",
        reply_markup=inline_edit_product_fields_keyboard(),
    )


async def handle_edit_new_flavor_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer("Название не может быть пустым.")
        return
    await state.update_data(new_flavor_name=name)
    await state.set_state(ProductEditStates.waiting_new_flavor_photo)
    await message.answer("Отправьте фото вкуса:")


async def handle_edit_new_flavor_photo(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    if not message.photo:
        await message.answer("Отправьте именно фото.")
        return
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    ext = os.path.splitext(file.file_path or ".jpg")[1] or ".jpg"
    filename = f"{uuid.uuid4()}{ext}"
    path = os.path.join(UPLOAD_DIR, filename)
    await message.bot.download_file(file.file_path, path)
    data = await state.get_data()
    name = data["new_flavor_name"]
    product_id = data["product_id"]
    service = ItemService(session)
    flavor = await service.create_flavor(name, filename)
    await service.add_flavor(product_id, flavor.id)
    await state.set_state(ProductEditStates.choosing_flavor)
    item = await service.get_item(product_id)
    names = ", ".join(f.name for f in item.flavors) if item.flavors else "пока нет"
    await message.answer(
        f"Вкус «{flavor.name}» создан и добавлен к товару. Вкусы: {names}.",
        reply_markup=inline_flavors_keyboard_edit(item.flavors, product_id),
    )


async def handle_flavor_edit_name_callback(
    callback: CallbackQuery, state: FSMContext
) -> None:
    try:
        await callback.answer()
    except TelegramBadRequest:
        pass
    flavor_id = int(callback.data.removeprefix(CBD_FLAVOR_EDIT_NAME_PREFIX))
    await state.update_data(flavor_id=flavor_id)
    await state.set_state(ProductEditStates.waiting_flavor_name)
    await callback.message.answer("Введите новое название вкуса:")


async def handle_flavor_edit_photo_callback(
    callback: CallbackQuery, state: FSMContext
) -> None:
    try:
        await callback.answer()
    except TelegramBadRequest:
        pass
    flavor_id = int(callback.data.removeprefix(CBD_FLAVOR_EDIT_PHOTO_PREFIX))
    await state.update_data(flavor_id=flavor_id)
    await state.set_state(ProductEditStates.waiting_flavor_photo)
    await callback.message.answer("Отправьте новое фото вкуса:")


async def handle_flavor_edit_back_callback(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    try:
        await callback.answer()
    except TelegramBadRequest:
        pass
    await state.set_state(ProductEditStates.choosing_flavor)
    data = await state.get_data()
    product_id = data.get("product_id")
    if not product_id:
        await callback.message.answer("Ошибка: товар не выбран.")
        return
    service = ItemService(session)
    item = await service.get_item(product_id)
    if not item:
        await callback.message.answer("Товар не найден.")
        return
    names = ", ".join(f.name for f in item.flavors) if item.flavors else "пока нет"
    await callback.message.answer(
        f"Вкусы товара: {names}. Выберите вкус для редактирования или «Добавить вкус».",
        reply_markup=inline_flavors_keyboard_edit(item.flavors, product_id),
    )


async def handle_edit_flavor_name_receive(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer("Название не может быть пустым.")
        return
    data = await state.get_data()
    flavor_id = data.get("flavor_id")
    if not flavor_id:
        await message.answer("Ошибка: вкус не выбран.")
        return
    service = ItemService(session)
    ok = await service.update_flavor_name(flavor_id, name)
    if not ok:
        await message.answer("Вкус не найден.")
        return
    product_id = data.get("product_id")
    item = await service.get_item(product_id)
    await state.set_state(ProductEditStates.choosing_flavor)
    names = ", ".join(f.name for f in item.flavors) if item.flavors else "пока нет"
    await message.answer(
        f"Название вкуса изменено. Вкусы товара: {names}.",
        reply_markup=inline_flavors_keyboard_edit(item.flavors, product_id),
    )


async def handle_edit_flavor_photo_receive(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    if not message.photo:
        await message.answer("Отправьте именно фото.")
        return
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    ext = os.path.splitext(file.file_path or ".jpg")[1] or ".jpg"
    filename = f"{uuid.uuid4()}{ext}"
    path = os.path.join(UPLOAD_DIR, filename)
    await message.bot.download_file(file.file_path, path)
    data = await state.get_data()
    flavor_id = data.get("flavor_id")
    if not flavor_id:
        await message.answer("Ошибка: вкус не выбран.")
        return
    service = ItemService(session)
    ok = await service.update_flavor_photo(flavor_id, filename)
    if not ok:
        await message.answer("Вкус не найден.")
        return
    product_id = data.get("product_id")
    item = await service.get_item(product_id)
    await state.set_state(ProductEditStates.choosing_flavor)
    names = ", ".join(f.name for f in item.flavors) if item.flavors else "пока нет"
    await message.answer(
        "Фото вкуса обновлено. Вкусы товара: " + names + ".",
        reply_markup=inline_flavors_keyboard_edit(item.flavors, product_id),
    )


async def _return_to_edit_keyboard(
    message: Message, state: FSMContext, success_text: str
) -> None:
    await state.set_state(ProductEditStates.choosing_field)
    await message.answer(
        success_text + "\n\nЧто ещё изменить? (по одному полю)",
        reply_markup=inline_edit_product_fields_keyboard(),
    )


async def handle_receive_name(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    new_name = (message.text or "").strip()
    if not new_name:
        await message.answer("Название не может быть пустым.")
        return
    data = await state.get_data()
    product_id = data["product_id"]
    service = ItemService(session)
    ok = await service.update_name(product_id, new_name)
    if ok:
        await _return_to_edit_keyboard(
            message, state, f"Название изменено на: «{new_name}»."
        )
    else:
        await message.answer("Товар не найден.")


async def handle_receive_description(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    new_desc = (message.text or "").strip()
    data = await state.get_data()
    product_id = data["product_id"]
    service = ItemService(session)
    ok = await service.update_description(product_id, new_desc)
    if ok:
        await _return_to_edit_keyboard(
            message, state, f"Описание изменено ({len(new_desc)} символов)."
        )
    else:
        await message.answer("Товар не найден.")


async def handle_receive_image(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    if not message.photo:
        await message.answer("Отправьте именно фото.")
        return
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    ext = os.path.splitext(file.file_path or ".jpg")[1] or ".jpg"
    filename = f"{uuid.uuid4()}{ext}"
    path = os.path.join(UPLOAD_DIR, filename)
    await message.bot.download_file(file.file_path, path)
    data = await state.get_data()
    product_id = data["product_id"]
    service = ItemService(session)
    ok = await service.update_photo(product_id, filename)
    if ok:
        await _return_to_edit_keyboard(message, state, "Фото товара обновлено.")
    else:
        await message.answer("Товар не найден.")


async def handle_receive_flavors(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    flavor_name = (message.text or "").strip()
    if not flavor_name:
        await message.answer("Введите название вкуса.")
        return
    data = await state.get_data()
    product_id = data["product_id"]
    service = ItemService(session)
    flavor = await service.get_flavor_by_name(flavor_name)
    if not flavor:
        await message.answer("Вкус с таким названием не найден.")
        return
    ok = await service.add_flavor(product_id, flavor.id)
    if ok:
        await _return_to_edit_keyboard(
            message, state, f"Вкус «{flavor_name}» добавлен к товару."
        )
    else:
        await message.answer("Товар не найден или ошибка.")

