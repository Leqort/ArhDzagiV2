import os
from uuid import uuid4

import aiofiles
from fastapi import APIRouter, Form, HTTPException, UploadFile, File
from sqlalchemy import select, delete

from config import UPLOAD_DIR
from database.db import SessionDep
from models.flavor import Flavor
from models.items import Item


router = APIRouter()


@router.post("/create_flavor")
async def create_flavor(
        name: str = Form(...),
        photo: UploadFile = File(...),
        session: SessionDep = None,
):
    extension = os.path.splitext(photo.filename)[1]
    file_name = f"{uuid4()}{extension}"
    file_path = os.path.join(UPLOAD_DIR, file_name)

    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await photo.read()
        await out_file.write(content)

    new_flavor = Flavor(
        name=name,
        photo=file_name
    )

    session.add(new_flavor)
    await session.commit()
    await session.refresh(new_flavor)

    return new_flavor


@router.post("/edit_flavor")
async def edit_flavor(
        id: int = Form(...),
        name: str = Form(...),
        photo: UploadFile = File(...),
        session: SessionDep = None,
):

    result = await session.execute(select(Flavor).where(Flavor.id == id))
    flavor = result.scalar_one_or_none()

    extension = os.path.splitext(photo.filename)[1]
    file_name = f"{uuid4()}{extension}"
    file_path = os.path.join(UPLOAD_DIR, file_name)

    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await photo.read()
        await out_file.write(content)

    if not flavor:
        raise HTTPException(status_code=404, detail="Вкус не найден")

    flavor.name = name
    flavor.photo = file_name

    await session.commit()
    await session.refresh(flavor)

    return flavor


@router.delete("/flavors/{flavor_id}")
async def delete_flavor(flavor_id: int, session: SessionDep):
    query = delete(Flavor).where(Flavor.id == flavor_id)
    result = await session.execute(query)
    await session.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Вкус не найден")

    return {"status": "deleted"}