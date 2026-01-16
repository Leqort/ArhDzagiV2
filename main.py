from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from database.db import engine, Base
from routes import items, flavors
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    await engine.dispose()


app = FastAPI(lifespan=lifespan)


app.mount("/static", StaticFiles(directory="uploads"), name="static")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# routes
app.include_router(items.router)
app.include_router(flavors.router)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)