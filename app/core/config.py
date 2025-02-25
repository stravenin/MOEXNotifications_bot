from os import getenv
from dotenv import load_dotenv

load_dotenv()

TG_TOKEN = getenv("TG_TOKEN")
THRUST_USERS = [int(getenv("THRUST_USER_ID"))]
T_TOKEN = getenv("T_TOKEN")

POSTGRES_USER = getenv("POSTGRES_USER")
POSTGRES_PASSWORD = getenv("POSTGRES_PASSWORD")
POSTGRES_DB = getenv("POSTGRES_DB")
POSTGRES_HOST = getenv("POSTGRES_HOST")
POSTGRES_PORT = getenv("POSTGRES_PORT")

