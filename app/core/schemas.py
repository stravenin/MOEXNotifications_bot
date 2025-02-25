from pydantic import BaseModel, Field
from typing import Optional

from app.core.models import str_4


class Notification(BaseModel):
    id: Optional[int] = None
    user_id: int
    ticker: str
    figi: str
    price: str
    target_price: str