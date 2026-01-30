import os
from typing import Annotated

from fastapi import Depends
from sqlalchemy import event, Engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# echo=True выводит все SQL-запросы; отключается через SQLALCHEMY_ECHO=0 или false
_sql_echo = os.getenv("SQLALCHEMY_ECHO", "0").lower() in ("1", "true", "yes")
engine = create_async_engine("sqlite+aiosqlite:///mydb.db", echo=_sql_echo)


new_async_session = async_sessionmaker(engine, expire_on_commit=False)

async def get_session():
    async with new_async_session() as session:
        yield session

SessionDep = Annotated[AsyncSession, Depends(get_session)]

class Base(DeclarativeBase):
    pass