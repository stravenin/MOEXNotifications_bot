from os import getenv
from dotenv import load_dotenv

load_dotenv()

TG_TOKEN = getenv("TG_TOKEN")
THRUST_USERS = [int(getenv("THRUST_USER_ID"))]
T_TOKEN = getenv("T_TOKEN")

