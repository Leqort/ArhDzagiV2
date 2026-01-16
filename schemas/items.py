from pydantic import BaseModel


class ItemSchema(BaseModel):
    name: str
    description: str
    price: float


class ItemGetSchema(BaseModel):
    id: int
    title: str
    author: str