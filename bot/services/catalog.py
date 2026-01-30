"""Сервис каталога товаров и вкусов."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.flavor import Flavor
from models.items import Item


class CatalogService:
    """Работа с каталогом (товары, вкусы)."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_flavors(self) -> list[tuple[int, str]]:
        """Список вкусов: [(id, name), ...]."""
        result = await self.session.execute(select(Flavor.id, Flavor.name).order_by(Flavor.name))
        return list(result.all())

    async def get_items_by_flavor(self, flavor_id: int | None) -> list[Item]:
        """Товары по вкусу. flavor_id=None — все товары."""
        q = select(Item)
        if flavor_id is not None:
            q = q.join(Item.flavors).where(Flavor.id == flavor_id)
        result = await self.session.execute(q)
        return list(result.scalars().unique().all())

    async def get_item_by_id(self, item_id: int) -> Item | None:
        """Товар по ID."""
        result = await self.session.execute(select(Item).where(Item.id == item_id))
        return result.scalar_one_or_none()
