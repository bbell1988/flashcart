from collections.abc import AsyncIterator

from app.config import settings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

engine = create_async_engine(settings.database_url)

async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncIterator[AsyncSession]:
    async with async_session_factory() as session:
        yield session