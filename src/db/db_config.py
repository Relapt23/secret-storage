from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import DBConfig
from app.core.models import Base

engine = create_async_engine(
    f"postgresql+asyncpg://{DBConfig.USER}:{DBConfig.PASSWORD}@{DBConfig.HOST}:{DBConfig.PORT}/{DBConfig.DATABASE}",
    echo=True
)

sess = async_sessionmaker(engine)


async def get_session():
    async with sess() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)