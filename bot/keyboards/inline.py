"""Inline-клавиатуры (привязаны к сообщению)."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Callback data для товаров
CBD_PRODUCT_DELETE_CANCEL = "product_delete_cancel"
CBD_PRODUCT_DELETE_CONFIRM_PREFIX = "product_delete_confirm:"
CBD_PRODUCT_EDIT_CANCEL = "product_edit_cancel"
CBD_PRODUCT_DELETE_PREFIX = "product_delete:"
CBD_PRODUCT_EDIT_PREFIX = "product_edit:"
CBD_PRODUCT_EDIT_FIELD = "product_edit_field"
CBD_EDIT_NAME = f"{CBD_PRODUCT_EDIT_FIELD}:name"
CBD_EDIT_DESCRIPTION = f"{CBD_PRODUCT_EDIT_FIELD}:description"
CBD_EDIT_IMAGE = f"{CBD_PRODUCT_EDIT_FIELD}:image"
CBD_EDIT_FLAVORS = f"{CBD_PRODUCT_EDIT_FIELD}:flavors"
CBD_EDIT_CATEGORY = f"{CBD_PRODUCT_EDIT_FIELD}:category"

# Редактирование вкуса (название, фото)
CBD_FLAVOR_EDIT_NAME_PREFIX = "flavor_edit_name:"
CBD_FLAVOR_EDIT_PHOTO_PREFIX = "flavor_edit_photo:"
CBD_FLAVOR_EDIT_BACK = "flavor_edit_back"

# Вкусы товара — инлайн под сообщением (добавление товара)
CBD_ADD_FLAVOR_SELECT_PREFIX = "add_flavor_select:"
CBD_ADD_FLAVOR_NEW = "add_flavor_new"
CBD_ADD_FLAVOR_DONE = "add_flavor_done"

# Вкусы товара — инлайн под сообщением (редактирование товара)
CBD_PRODUCT_EDIT_FLAVOR_PREFIX = "product_edit_flavor:"
CBD_EDIT_FLAVOR_ADD_PREFIX = "edit_flavor_add:"
CBD_PRODUCT_EDIT_FLAVORS_BACK = "product_edit_flavors_back"

# Категории: удаление и редактирование
CBD_CATEGORY_DELETE_PREFIX = "category_delete:"
CBD_CATEGORY_DELETE_CANCEL = "category_delete_cancel"
CBD_CATEGORY_DELETE_CONFIRM_PREFIX = "category_delete_confirm:"
CBD_CATEGORY_EDIT_PREFIX = "category_edit:"
CBD_CATEGORY_EDIT_CANCEL = "category_edit_cancel"
CBD_CATEGORY_EDIT_FIELD_NAME = "category_edit_field:name"
CBD_CATEGORY_EDIT_FIELD_IMAGE = "category_edit_field:image"
# Выбор категории для товара (создание/редактирование)
CBD_PRODUCT_SELECT_CATEGORY_PREFIX = "product_select_category:"


def inline_delete_product_keyboard(items: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    """Клавиатура выбора товара для удаления. items — список (id, название)."""
    buttons = [
        [InlineKeyboardButton(text=f"🗑 {name} (ID: {id_})", callback_data=f"{CBD_PRODUCT_DELETE_PREFIX}{id_}")]
        for id_, name in items
    ]
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data=CBD_PRODUCT_DELETE_CANCEL)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def inline_confirm_delete_product_keyboard(item_id: int) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения удаления товара: Да, удалить / Отмена."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"{CBD_PRODUCT_DELETE_CONFIRM_PREFIX}{item_id}"),
                InlineKeyboardButton(text="❌ Отмена", callback_data=CBD_PRODUCT_DELETE_CANCEL),
            ],
        ]
    )


def inline_edit_product_start_keyboard(items: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    """Клавиатура выбора товара для редактирования. items — список (id, название)."""
    buttons = [
        [InlineKeyboardButton(text=f"✏️ {name} (ID: {id_})", callback_data=f"{CBD_PRODUCT_EDIT_PREFIX}{id_}")]
        for id_, name in items
    ]
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data=CBD_PRODUCT_EDIT_CANCEL)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def inline_edit_product_fields_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура к сообщению «Что изменить?» (под сообщением)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📝 Название", callback_data=CBD_EDIT_NAME),
                InlineKeyboardButton(text="📄 Описание", callback_data=CBD_EDIT_DESCRIPTION),
            ],
            [
                InlineKeyboardButton(text="🖼 Картинка", callback_data=CBD_EDIT_IMAGE),
                InlineKeyboardButton(text="🍬 Вкусы", callback_data=CBD_EDIT_FLAVORS),
            ],
            [InlineKeyboardButton(text="❌ Отмена", callback_data=CBD_PRODUCT_EDIT_CANCEL)],
        ]
    )


def inline_edit_cancel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура «Отмена» к сообщениям ввода (название, описание, фото, вкус)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data=CBD_PRODUCT_EDIT_CANCEL)]
        ]
    )


def inline_edit_flavor_keyboard(flavor_id: int) -> InlineKeyboardMarkup:
    """Клавиатура под сообщением «Вкус: … Что изменить?»: название, фото, назад."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📝 Название", callback_data=f"{CBD_FLAVOR_EDIT_NAME_PREFIX}{flavor_id}"),
                InlineKeyboardButton(text="🖼 Фото", callback_data=f"{CBD_FLAVOR_EDIT_PHOTO_PREFIX}{flavor_id}"),
            ],
            [InlineKeyboardButton(text="❌ Назад", callback_data=CBD_FLAVOR_EDIT_BACK)],
        ]
    )


def inline_flavors_keyboard_add(flavors: list, selected_ids: set[int]) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура выбора вкусов при добавлении товара (прикреплена к сообщению).
    flavors — список Flavor; selected_ids — множество выбранных id. Вкусы уникальны (без дубликатов по id).
    """
    seen_ids: set[int] = set()
    buttons = []
    for f in flavors:
        if f.id in seen_ids:
            continue
        seen_ids.add(f.id)
        text = f"✓ {f.name}" if f.id in selected_ids else f.name
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"{CBD_ADD_FLAVOR_SELECT_PREFIX}{f.id}")])
    buttons.append([
        InlineKeyboardButton(text="🍬 Добавить вкус", callback_data=CBD_ADD_FLAVOR_NEW),
        InlineKeyboardButton(text="✅ Готово", callback_data=CBD_ADD_FLAVOR_DONE),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def inline_delete_category_keyboard(categories: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    """Клавиатура выбора категории для удаления. categories — список (id, название)."""
    buttons = [
        [InlineKeyboardButton(text=f"🗑 {name} (ID: {id_})", callback_data=f"{CBD_CATEGORY_DELETE_PREFIX}{id_}")]
        for id_, name in categories
    ]
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data=CBD_CATEGORY_DELETE_CANCEL)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def inline_confirm_delete_category_keyboard(category_id: int) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения удаления категории."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"{CBD_CATEGORY_DELETE_CONFIRM_PREFIX}{category_id}"),
                InlineKeyboardButton(text="❌ Отмена", callback_data=CBD_CATEGORY_DELETE_CANCEL),
            ],
        ]
    )


def inline_edit_category_start_keyboard(categories: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    """Клавиатура выбора категории для редактирования."""
    buttons = [
        [InlineKeyboardButton(text=f"✏️ {name} (ID: {id_})", callback_data=f"{CBD_CATEGORY_EDIT_PREFIX}{id_}")]
        for id_, name in categories
    ]
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data=CBD_CATEGORY_EDIT_CANCEL)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def inline_edit_category_fields_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура «Что изменить у категории?»: название или картинка."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📝 Название", callback_data=CBD_CATEGORY_EDIT_FIELD_NAME),
                InlineKeyboardButton(text="🖼 Картинка", callback_data=CBD_CATEGORY_EDIT_FIELD_IMAGE),
            ],
            [InlineKeyboardButton(text="❌ Отмена", callback_data=CBD_CATEGORY_EDIT_CANCEL)],
        ]
    )


def inline_edit_category_cancel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура «Отмена» при вводе названия/картинки категории."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data=CBD_CATEGORY_EDIT_CANCEL)]
        ]
    )


def inline_select_category_keyboard(categories: list) -> InlineKeyboardMarkup:
    """Клавиатура выбора категории для товара (создание/редактирование). categories — список Category."""
    buttons = [
        [InlineKeyboardButton(text=c.name, callback_data=f"{CBD_PRODUCT_SELECT_CATEGORY_PREFIX}{c.id}")]
        for c in categories
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def inline_flavors_keyboard_edit(item_flavors: list, product_id: int) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура вкусов товара при редактировании (прикреплена к сообщению).
    item_flavors — список вкусов только этого товара; показываем уникальные по id. product_id — id товара.
    """
    seen_ids: set[int] = set()
    buttons = []
    for f in item_flavors:
        if f.id in seen_ids:
            continue
        seen_ids.add(f.id)
        buttons.append([InlineKeyboardButton(text=f.name, callback_data=f"{CBD_PRODUCT_EDIT_FLAVOR_PREFIX}{f.id}")])
    buttons.append([
        InlineKeyboardButton(text="🍬 Добавить вкус", callback_data=f"{CBD_EDIT_FLAVOR_ADD_PREFIX}{product_id}"),
        InlineKeyboardButton(text="◀️ Назад", callback_data=CBD_PRODUCT_EDIT_FLAVORS_BACK),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
