import asyncio
import platform
import os
from functools import wraps
from typing import List, Callable

from dotenv import load_dotenv

from sqlalchemy import select, delete
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.models import NotificationsModel, NotificationModel
from app.core.schemas import NotificationSchema

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

load_dotenv()

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
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



def filter_system_data(nt: NotificationsModel) -> dict:
    """Фильтрует данные, удаляя системные."""
    exclude_fields = {"_sa_instance_state"}

    data = {k: v for k, v in nt.__dict__.items() if k not in exclude_fields}

    return data


class db:


    @staticmethod
    @db_exception_handler
    @with_db_session
    async def add_notification(session: AsyncSession, nt: NotificationSchema):
        nt_dict = nt.model_dump()


        raw = NotificationModel(**nt_dict)
        session.add(raw)
        await session.flush()

        return filter_system_data(raw)

    @staticmethod
    @db_exception_handler
    @with_db_session
    async def get_notifications_by_user_id(session: AsyncSession, user_id: int):
        user_from_db = (await session.execute(select(NotificationModel).where(NotificationModel.user_id == user_id))).all()
        return filter_sensitive_data(user_from_db) if user_from_db else None




    @staticmethod
    @db_exception_handler
    @with_db_session
    async def get_user_by_nickname(session: AsyncSession, nickname: str) -> User | None:
        user_from_db = (await session.execute(select(UserModel).where(UserModel.nickname == nickname))).scalar()
        return User(**filter_to_user_data(user_from_db)) if user_from_db else None

    @staticmethod
    @db_exception_handler
    @with_db_session
    async def update_user(session: AsyncSession, user: User):
        user_to_update = (await session.execute(select(UserModel).where(UserModel.id == user.id))).scalar()

        if not user_to_update:
            return False

        # Словарь с полями для обновления
        update_fields = {
            "nickname": user.nickname,
            "password": user.password,
            "cert": user.cert,
            "user_role_id": user.user_role_id,
            "block_at": user.block_at,
            "version_history": user.version_history
        }

        # Применяем изменения только для непустых полей
        for field, value in update_fields.items():
            if value is not None and value != "":
                if field == "password":
                    user_to_update.password_hash = get_password_hash(value)
                elif field == "cert":
                    user_to_update.cert_hash = get_encrypted_cert(value)
                else:
                    setattr(user_to_update, field, value)

        await session.commit()

        redis_client = RedisConnection.get_client()
        await redis_client.delete("get_all_users")
        await redis_client.delete(f"get_user_by_id:{user.id}")

        return True

    @staticmethod
    @db_exception_handler
    @with_db_session
    async def delete_users(session: AsyncSession,user_ids: List[int]) -> bool:
        await session.execute(delete(UserModel).where(UserModel.id.in_(user_ids)))
        return True

    @staticmethod
    @db_exception_handler
    @with_db_session
    @cached_with_redis(ttl=3600)
    async def get_all_users(session: AsyncSession) -> List[dict]:
        users_from_db = await session.execute(select(UserModel))
        return [filter_sensitive_data(user[0]) for user in users_from_db]

    @staticmethod
    @db_exception_handler
    @with_db_session
    @cached_with_redis(ttl=3600)
    async def get_all_roles(session: AsyncSession) -> List[dict]:
        roles_from_db = (await session.execute(select(RoleModel)))
        return [filter_service_data(role[0]) for role in roles_from_db]

    @staticmethod
    @db_exception_handler
    @with_db_session
    async def get_role_by_id(session: AsyncSession, role_id: int):
        role_from_db = (await session.execute(select(RoleModel).where(RoleModel.id == role_id))).scalar()
        return filter_service_data(role_from_db) if role_from_db else None

# user = User(
#     # id=4,
#     nickname="user",
#     password="user",
#     user_role_id=1,
#     # role_id="2",
# #     avatar_url=user.avatar_url,
# #     active_is=True,
#
# )
# async def r():
#     u = await db.add_user(user)
#     print(u)
# asyncio.run(r())