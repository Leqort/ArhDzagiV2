import os
from uuid import uuid4

import aiofiles
from fastapi import APIRouter, Form, HTTPException, UploadFile, File
from sqlalchemy import select

from config import UPLOAD_DIR
from database.db import SessionDep
from models.category import Category

router = APIRouter()


@router.get("/get_categories")
async def get_categories(session: SessionDep):
    """Получить список всех категорий."""
    result = await session.execute(select(Category).order_by(Category.name))
    return list(result.scalars().all())


@router.post("/create_category")
async def create_category(
    name: str = Form(...),
    photo: UploadFile = File(...),
    session: SessionDep = None,
):
    extension = os.path.splitext(photo.filename or "")[1] or ".jpg"
    file_name = f"{uuid4()}{extension}"
    file_path = os.path.join(UPLOAD_DIR, file_name)

    async with aiofiles.open(file_path, "wb") as out_file:
        content = await photo.read()
        await out_file.write(content)

    try:
        new_category = Category(name=name.strip(), photo=file_name)
        session.add(new_category)
        await session.commit()
        await session.refresh(new_category)
        return new_category
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка БД: {str(e)}")


@router.delete("/categories/{category_id}")
async def delete_category(category_id: int, session: SessionDep):
    result = await session.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    if category.photo:
        file_path = os.path.join(UPLOAD_DIR, category.photo)
        if os.path.exists(file_path):
            os.remove(file_path)
    await session.delete(category)
    await session.commit()
    return {"status": "deleted"}


@router.patch("/categories/{category_id}")
async def update_category(
    category_id: int,
    session: SessionDep,
    name: str = Form(None),
    photo: UploadFile = File(None),
):
    """Обновить название и/или картинку категории."""
    result = await session.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    if name is not None and name.strip():
        category.name = name.strip()
    if photo is not None and photo.filename:
        extension = os.path.splitext(photo.filename)[1] or ".jpg"
        file_name = f"{uuid4()}{extension}"
        file_path = os.path.join(UPLOAD_DIR, file_name)
        async with aiofiles.open(file_path, "wb") as out_file:
            content = await photo.read()
            await out_file.write(content)
        if category.photo:
            old_path = os.path.join(UPLOAD_DIR, category.photo)
            if os.path.exists(old_path):
                os.remove(old_path)
        category.photo = file_name
    await session.commit()
    await session.refresh(category)
    return category
