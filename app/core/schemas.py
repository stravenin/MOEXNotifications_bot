from pydantic import BaseModel
from typing import Optional


class Notification(BaseModel):
    id: Optional[int] = None
    user_id: int
    ticker: str
    figi: str
    price: str
    target_price: str