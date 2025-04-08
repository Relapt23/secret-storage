from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.app import endpoints
from src.db.db_config import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(endpoints.router)
