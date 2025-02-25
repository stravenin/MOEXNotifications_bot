import asyncio
import platform
from functools import wraps
from typing import List

from sqlalchemy import select, delete
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.models import NotificationModel
from app.core.schemas import Notification
from app.core.config import (
    POSTGRES_USER,
    POSTGRES_PASSWORD,
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PORT
)

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


DB_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

async_engine = create_async_engine(
    url=DB_URL,
    echo=True,
    poolclass=NullPool,
)

async_session = async_sessionmaker(async_engine)



def db_exception_handler(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            print(f"[x] Database error: {e}")
            return None
    return wrapper

def with_db_session(func):
    """Декоратор для автоматического создания сессии и обработки ошибок БД."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        async with async_session.begin() as session:
            return await func(session, *args, **kwargs)
    return wrapper



def filter_system_data(nt: NotificationModel) -> dict:
    """Фильтрует данные, удаляя системные."""
    exclude_fields = {"_sa_instance_state"}

    data = {k: v for k, v in nt.__dict__.items() if k not in exclude_fields}

    return data


class db:


    @staticmethod
    @db_exception_handler
    @with_db_session
    async def add_notification(session: AsyncSession, nt: Notification):
        nt_dict = nt.model_dump()


        raw = NotificationModel(**nt_dict)
        session.add(raw)
        await session.flush()

        return Notification(**filter_system_data(raw))

    @staticmethod
    @db_exception_handler
    @with_db_session
    async def get_notifications_by_user_id(session: AsyncSession, user_id: int):
        raw = (await session.execute(select(NotificationModel).where(NotificationModel.user_id == user_id))).all()
        print(f"{raw=}")
        return [Notification(**filter_system_data(r[0])) for r in raw]

    @staticmethod
    @db_exception_handler
    @with_db_session
    async def get_notification_by_id(session: AsyncSession, _id: int):
        raw = (await session.execute(select(NotificationModel).where(NotificationModel.id == _id))).scalar()
        print(f"{raw=}")
        return Notification(**filter_system_data(raw))



    @staticmethod
    @db_exception_handler
    @with_db_session
    async def delete_notifications_by_id(session: AsyncSession,ids: List[int]) -> bool:
        await session.execute(delete(NotificationModel).where(NotificationModel.id.in_(ids)))
        return True

    @staticmethod
    @db_exception_handler
    @with_db_session
    async def get_all_notifications(session: AsyncSession) -> List[Notification]:
        raw = (await session.execute(select(NotificationModel))).all()
        return [Notification(**filter_system_data(user[0])) for user in raw]


# nt = Notification(
#     user_id=1221,
#     ticker="HEAD",
#     price="3900",
#     target_price="5100",
#     figi="figi"
# )
# async def r():
#     u = await db.get_all_notifications()
#     print(u)
# asyncio.run(r())