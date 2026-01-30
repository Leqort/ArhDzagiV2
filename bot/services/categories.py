"""Сервис категорий для бота (работа с БД через сессию)."""
import os

from sqlalchemy import select

from config import UPLOAD_DIR
from models.category import Category
from sqlalchemy.ext.asyncio import AsyncSession


class CategoryService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_categories(self) -> list[Category]:
        result = await self.session.execute(select(Category).order_by(Category.name))
        return list(result.scalars().all())

    async def get_category(self, category_id: int) -> Category | None:
        return await self.session.get(Category, category_id)

    async def create_category(self, name: str, photo_filename: str) -> Category:
        category = Category(name=name.strip(), photo=photo_filename)
        self.session.add(category)
        await self.session.commit()
        await self.session.refresh(category)
        return category

    async def delete_category(self, category_id: int) -> bool:
        category = await self.get_category(category_id)
        if not category:
            return False
        if category.photo:
            file_path = os.path.join(UPLOAD_DIR, category.photo)
            if os.path.exists(file_path):
                os.remove(file_path)
        await self.session.delete(category)
        await self.session.commit()
        return True

    async def update_category_name(self, category_id: int, name: str) -> bool:
        category = await self.get_category(category_id)
        if not category:
            return False
        category.name = name.strip()
        await self.session.commit()
        return True

    async def update_category_photo(self, category_id: int, photo_filename: str) -> bool:
        category = await self.get_category(category_id)
        if not category:
            return False
        if category.photo:
            old_path = os.path.join(UPLOAD_DIR, category.photo)
            if os.path.exists(old_path):
                os.remove(old_path)
        category.photo = photo_filename
        await self.session.commit()
        return True
