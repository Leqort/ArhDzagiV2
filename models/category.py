from typing import List

from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(unique=True)
    photo: Mapped[str]

    items: Mapped[List["Item"]] = relationship(
        "Item",
        back_populates="category",
    )
