import logging
from functools import wraps

from tinkoff.invest import AsyncClient
from tinkoff.invest.constants import INVEST_GRPC_API
from tinkoff.invest.schemas import InstrumentIdType

from app.core.schemas import Notification
from app.models.notification import NotificationModel
from app.utils.unitofwork import IUnitOfWork

from app.core.config import settings

def db_exception_handler(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logging.log(level=logging.ERROR, msg=f"Database error: {e}")
            return None
    return wrapper

class NotificationService:
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow


    @db_exception_handler
    async def add_notification(self, data: dict[str, str], user_id: int):
        async with self.uow:
            ticker = data.get("ticker")
            target_price = data.get("target_price")

            figi = await self.get_share_figi_by_ticker(ticker)
            price = await self.get_current_price_by_figi(figi)

            nt = Notification(
                user_id=user_id,
                ticker=ticker,
                target_price=target_price,
                price=price,
                figi=figi
            )
            nt_dict = nt.model_dump()
            raw = NotificationModel(**nt_dict)

            response = await self.uow.notification.create_notification(raw)

            change_percent = (float(nt.target_price) - float(nt.price)) / float(nt.price) * 100

            return change_percent if response else None

    @db_exception_handler
    async def get_notifications_by_user_id(self, user_id: int):
        async with self.uow:
            response = await self.uow.notification.get_notifications_by_user_id(user_id)
            return [Notification(**raw.filter_system_data()) for raw in response]

    @db_exception_handler
    async def get_notification_by_id(self, _id: int):
        async with self.uow:
            response = await self.uow.notification.get_notification_by_id(_id)
            return Notification(**response.filter_system_data())

    @db_exception_handler
    async def delete_notification_by_id(self, _id: int):
        async with self.uow:
            return await self.uow.notification.delete_notification_by_id(_id)

    @db_exception_handler
    async def get_all_user_ids(self):
        async with self.uow:
            return await self.uow.notification.get_all_user_ids()

    def _get_nano_without_zero(self, nano: str) -> str:
        real_nano = nano.rstrip("0")
        return real_nano if real_nano else "0"

    async def get_current_price_by_figi(self, figi: str) -> str:
        async with (AsyncClient(settings.T_TOKEN, target=INVEST_GRPC_API) as client):
            raw = await client.market_data.get_last_prices(figi=[figi])

            nano = str(raw.last_prices[0].price.nano)
            units = str(raw.last_prices[0].price.units)

            real_nano = self._get_nano_without_zero(nano)

            return units + "." + real_nano

    async def get_share_figi_by_ticker(self, ticker: str, market: str = "TQBR") -> str:
        async with (AsyncClient(settings.T_TOKEN, target=INVEST_GRPC_API) as client):
            instruments = await client.instruments.share_by(
                id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_TICKER,
                class_code=market, id=ticker)
            return instruments.instrument.figi

    async def get_current_price_by_ticker(self, ticker: str) -> str:
        async with (AsyncClient(settings.T_TOKEN, target=INVEST_GRPC_API) as client):
            figi = await self.get_share_figi_by_ticker(ticker)

            price = await client.market_data.get_last_prices(figi=[figi])

            nano = str(price.last_prices[0].price.nano)
            units = str(price.last_prices[0].price.units)

            real_nano = self._get_nano_without_zero(nano)

            return units + "." + real_nano
