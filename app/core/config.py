from os import getenv
from dotenv import load_dotenv

load_dotenv()
class Settings:

    TG_TOKEN = getenv("TG_TOKEN")
    ADMIN_USERS = [int(getenv("ADMIN_USER_ID"))]
    T_TOKEN = getenv("T_TOKEN")

    POSTGRES_USER = getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = getenv("POSTGRES_PASSWORD")
    POSTGRES_DB = getenv("POSTGRES_DB")
    POSTGRES_HOST = getenv("POSTGRES_HOST")
    POSTGRES_PORT = getenv("POSTGRES_PORT")
    ASYNC_DB_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    DB_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

settings = Settings()

