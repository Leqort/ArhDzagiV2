from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db import Base

item_flavor_association = Table(
    "item_flavor_association",
    Base.metadata,
    Column("item_id", ForeignKey("items.id", ondelete="CASCADE"), primary_key=True),
    Column("flavor_id", ForeignKey("flavors.id", ondelete="CASCADE"), primary_key=True),
)


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]
    description: Mapped[str]
    price: Mapped[float]
    discount: Mapped[float] = mapped_column(nullable=True)
    photo: Mapped[str]
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )

    category: Mapped["Category"] = relationship("Category", back_populates="items")
    flavors: Mapped[list["Flavor"]] = relationship(
        secondary="item_flavor_association",
        back_populates="items",
    )