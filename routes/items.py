import os

from sqlalchemy.orm import selectinload

from config import UPLOAD_DIR
from database.db import SessionDep
from models.category import Category
from models.flavor import Flavor
from models.items import Item
from uuid import uuid4
from fastapi import Form, UploadFile, File, APIRouter, HTTPException
from sqlalchemy import select
import aiofiles

router = APIRouter()


@router.post("/create_items")
async def create_item(
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    category_id: int = Form(...),
    discount: float = Form(None),
    flavor_ids: str = Form(None),
    photo: UploadFile = File(...),
    session: SessionDep = None,
):
    if not category_id:
        raise HTTPException(status_code=400, detail="Категория обязательна для товара")
    category = await session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Категория не найдена")

    extension = os.path.splitext(photo.filename)[1]
    file_name = f"{uuid4()}{extension}"
    file_path = os.path.join(UPLOAD_DIR, file_name)

    async with aiofiles.open(file_path, "wb") as out_file:
        content = await photo.read()
        await out_file.write(content)

    selected_flavors = []
    if flavor_ids:
        try:
            id_list = [int(x.strip()) for x in flavor_ids.split(",") if x.strip()]
            result = await session.execute(select(Flavor).where(Flavor.id.in_(id_list)))
            selected_flavors = result.scalars().all()
            if len(selected_flavors) != len(id_list):
                raise HTTPException(status_code=404, detail="Один или несколько вкусов не найдены")
        except ValueError:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=400,
                detail="flavor_ids должен быть строкой чисел через запятую (например: '1,2,3')",
            )

    try:
        new_item = Item(
            name=name,
            description=description,
            price=price,
            discount=discount,
            category_id=category_id,
            flavors=selected_flavors,
            photo=file_name,
        )
        session.add(new_item)
        await session.commit()
        await session.refresh(new_item)
        return new_item
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка БД: {str(e)}")


@router.get("/get_items")
async def get_items(session: SessionDep, category_id: int | None = None):
    query = select(Item).options(
        selectinload(Item.flavors),
        selectinload(Item.category),
    )
    if category_id is not None:
        query = query.where(Item.category_id == category_id)
    result = await session.execute(query)
    return list(result.scalars().unique().all())


@router.get("/items/{item_id}/flavors")
async def get_item_flavors(item_id: int, session: SessionDep):
    stmt = select(Item).where(Item.id == item_id).options(selectinload(Item.flavors))
    result = await session.execute(stmt)
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Товар не найден")

    return item.flavors


@router.delete("/items/{item_id}")
async def delete_item(item_id: int, session: SessionDep):

    result = await session.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Товар не найден")

    if item.photo:
        file_path = os.path.join(UPLOAD_DIR, item.photo)
        if os.path.exists(file_path):
            os.remove(file_path)

    await session.delete(item)
    await session.commit()

    return {"status": "success", "message": f"Item {item_id} and its relations deleted"}


@router.post("/add_flavor_to_item")
async def add_flavor_to_item(item_id: int, flavor_id: int, session: SessionDep):
    stmt = select(Item).where(Item.id == item_id).options(selectinload(Item.flavors))
    result = await session.execute(stmt)
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Товар не найден")

    flavor = await session.get(Flavor, flavor_id)
    if not flavor:
        raise HTTPException(status_code=404, detail="Вкус не найден")

    if any(f.id == flavor.id for f in item.flavors):
        return {"message": "Этот вкус уже добавлен"}

    item.flavors.append(flavor)
    await session.commit()
    return {"status": "success"}


@router.post("/remove_flavor_from_item")
async def remove_taste_from_item(item_id: int, flavor_id: int, session: SessionDep):
    stmt = select(Item).where(Item.id == item_id).options(selectinload(Item.flavors))
    result = await session.execute(stmt)
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Товар не найден")

    flavor = await session.get(Flavor, flavor_id)
    if not flavor:
        raise HTTPException(status_code=404, detail="Вкус не найден")

    item.flavors.remove(flavor)
    await session.commit()
    return {"status": "success"}


@router.patch("/items/{item_id}")
async def update_item(
    item_id: int,
    session: SessionDep,
    category_id: int = Form(None),
):
    """Обновить категорию товара (и при необходимости другие поля)."""
    result = await session.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Товар не найден")
    if category_id is not None:
        cat = await session.get(Category, category_id)
        if not cat:
            raise HTTPException(status_code=404, detail="Категория не найдена")
        item.category_id = category_id
    await session.commit()
    await session.refresh(item)
    return item