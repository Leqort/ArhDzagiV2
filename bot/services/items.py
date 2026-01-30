"""Сервис товаров: добавление, удаление, редактирование (логика бэкенда для бота)."""
import os

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from config import UPLOAD_DIR
from models.flavor import Flavor
from models.items import Item
from sqlalchemy.ext.asyncio import AsyncSession


class ItemService:
    """Работа с товарами (Item): создание, удаление, обновление полей и вкусов."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_item(self, item_id: int) -> Item | None:
        """Товар по ID с подгрузкой вкусов."""
        result = await self.session.execute(
            select(Item).where(Item.id == item_id).options(selectinload(Item.flavors))
        )
        return result.scalar_one_or_none()

    async def get_items(self) -> list[Item]:
        """Список всех товаров с вкусами."""
        result = await self.session.execute(
            select(Item).options(selectinload(Item.flavors)).order_by(Item.id)
        )
        return list(result.scalars().unique().all())

    async def get_flavors(self) -> list[Flavor]:
        """Список всех вкусов."""
        result = await self.session.execute(select(Flavor).order_by(Flavor.name))
        return list(result.scalars().all())

    async def get_flavors_by_ids(self, flavor_ids: list[int]) -> list[Flavor]:
        """Список вкусов по списку id (только вкусы, относящиеся к выбранным id)."""
        if not flavor_ids:
            return []
        result = await self.session.execute(
            select(Flavor).where(Flavor.id.in_(flavor_ids)).order_by(Flavor.name)
        )
        return list(result.scalars().all())

    async def create_item(
        self,
        name: str,
        description: str,
        price: float,
        photo_filename: str,
        discount: float | None = None,
        flavor_ids: list[int] | None = None,
    ) -> Item:
        """Создать товар. photo_filename — имя файла в UPLOAD_DIR."""
        selected_flavors: list[Flavor] = []
        if flavor_ids:
            result = await self.session.execute(select(Flavor).where(Flavor.id.in_(flavor_ids)))
            selected_flavors = list(result.scalars().all())
        item = Item(
            name=name,
            description=description,
            price=price,
            discount=discount,
            photo=photo_filename,
            flavors=selected_flavors,
        )
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def delete_item(self, item_id: int) -> bool:
        """Удалить товар и файл фото. Возвращает True, если товар был найден."""
        item = await self.get_item(item_id)
        if not item:
            return False
        if item.photo:
            file_path = os.path.join(UPLOAD_DIR, item.photo)
            if os.path.exists(file_path):
                os.remove(file_path)
        await self.session.delete(item)
        await self.session.commit()
        return True

    async def update_name(self, item_id: int, name: str) -> bool:
        """Обновить название товара."""
        item = await self.get_item(item_id)
        if not item:
            return False
        item.name = name
        await self.session.commit()
        return True

    async def update_description(self, item_id: int, description: str) -> bool:
        """Обновить описание товара."""
        item = await self.get_item(item_id)
        if not item:
            return False
        item.description = description
        await self.session.commit()
        return True

    async def update_photo(self, item_id: int, new_photo_filename: str) -> bool:
        """Обновить фото товара. Старый файл удаляется."""
        item = await self.get_item(item_id)
        if not item:
            return False
        if item.photo:
            old_path = os.path.join(UPLOAD_DIR, item.photo)
            if os.path.exists(old_path):
                os.remove(old_path)
        item.photo = new_photo_filename
        await self.session.commit()
        return True

    async def add_flavor(self, item_id: int, flavor_id: int) -> bool:
        """Добавить вкус к товару (по одному)."""
        item = await self.get_item(item_id)
        if not item:
            return False
        flavor = await self.session.get(Flavor, flavor_id)
        if not flavor:
            return False
        if any(f.id == flavor.id for f in item.flavors):
            return True  # уже есть
        item.flavors.append(flavor)
        await self.session.commit()
        return True

    async def remove_flavor(self, item_id: int, flavor_id: int) -> bool:
        """Убрать вкус у товара."""
        item = await self.get_item(item_id)
        if not item:
            return False
        flavor = await self.session.get(Flavor, flavor_id)
        if not flavor:
            return False
        if flavor in item.flavors:
            item.flavors.remove(flavor)
            await self.session.commit()
        return True

    async def get_flavor_by_name(self, name: str) -> Flavor | None:
        """Вкус по названию."""
        result = await self.session.execute(select(Flavor).where(Flavor.name == name.strip()))
        return result.scalar_one_or_none()

    async def get_flavor(self, flavor_id: int) -> Flavor | None:
        """Вкус по ID."""
        return await self.session.get(Flavor, flavor_id)

    async def create_flavor(self, name: str, photo_filename: str) -> Flavor:
        """Создать новый вкус. photo_filename — имя файла в UPLOAD_DIR."""
        flavor = Flavor(name=name.strip(), photo=photo_filename)
        self.session.add(flavor)
        await self.session.commit()
        await self.session.refresh(flavor)
        return flavor

    async def update_flavor_name(self, flavor_id: int, name: str) -> bool:
        """Изменить название вкуса."""
        flavor = await self.session.get(Flavor, flavor_id)
        if not flavor:
            return False
        flavor.name = name.strip()
        await self.session.commit()
        return True

    async def update_flavor_photo(self, flavor_id: int, photo_filename: str) -> bool:
        """Изменить фото вкуса. Старый файл удаляется."""
        flavor = await self.session.get(Flavor, flavor_id)
        if not flavor:
            return False
        if flavor.photo:
            old_path = os.path.join(UPLOAD_DIR, flavor.photo)
            if os.path.exists(old_path):
                os.remove(old_path)
        flavor.photo = photo_filename
        await self.session.commit()
        return True
