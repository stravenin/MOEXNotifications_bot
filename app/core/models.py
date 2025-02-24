from typing import Annotated

from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped

str_4 = Annotated[str, 4]
str_15 = Annotated[str, 15]

class Base(DeclarativeBase):
    type_annotation_map = {
        str_4: String(length=4),
        str_15: String(length=15),
    }


class NotificationModel(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int]
    ticker: Mapped[str_4]
    figi: Mapped[str_15]
    price: Mapped[str_15]
    target_price: Mapped[str_15]
