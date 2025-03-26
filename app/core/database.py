from typing import Annotated

from sqlalchemy import AsyncAdaptedQueuePool, String
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

str_4 = Annotated[str, 4]
str_15 = Annotated[str, 15]

class Base(DeclarativeBase):
    type_annotation_map = {
        str_4: String(length=4),
        str_15: String(length=15),
    }



engine = create_async_engine(
    settings.ASYNC_DB_URL,
    echo=True,
    future=True,
    pool_size=75,
    max_overflow=125,
    pool_recycle=600,
    pool_pre_ping=True,
    poolclass=AsyncAdaptedQueuePool,
)

async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

