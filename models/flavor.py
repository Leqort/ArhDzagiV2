from typing import List

from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db import Base
from models.items import item_flavor_association


class Flavor(Base):
    __tablename__ = "flavors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    photo: Mapped[str]

    items: Mapped[List["Item"]] = relationship(
        secondary=item_flavor_association, back_populates="flavors"
    )