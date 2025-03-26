from sqlalchemy.orm import mapped_column, Mapped

from app.core.database import Base, str_4, str_15


class NotificationModel(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(index=True)
    ticker: Mapped[str_4]
    figi: Mapped[str_15]
    price: Mapped[str_15]
    target_price: Mapped[str_15]

    def filter_system_data(self) -> dict:
        """Фильтрует данные, удаляя системные."""
        exclude_fields = {"_sa_instance_state"}

        data = {k: v for k, v in self.__dict__.items() if k not in exclude_fields}

        return data

    def __repr__(self):
        return (f"NotificationModel<{self.id=}, "
                f"{self.user_id=}, {self.ticker=}, "
                f"{self.figi=}, {self.price=}, {self.target_price=}>")
