from functools import wraps
from typing import Callable

from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram import html, Router, F
from aiogram.fsm.state import State, StatesGroup


from tinkoff.invest import AsyncClient, CandleInterval
from tinkoff.invest.constants import INVEST_GRPC_API, INVEST_GRPC_API_SANDBOX
from tinkoff.invest.schemas import CandleSource, InstrumentIdType, InstrumentStatus

from app.keyboards import StartKeyboard
from app.middlewares import AuthMiddleware
from config import THRUST_USERS, T_TOKEN

router = Router()

router.message.outer_middleware(AuthMiddleware())

class CreateNotification(StatesGroup):
    ticker = State()
    price = State()



async def get_current_price_by_ticker(ticker: str, market: str = "TQBR") -> str:
    async with (AsyncClient(T_TOKEN, target=INVEST_GRPC_API) as client):
        instruments = await client.instruments.share_by(id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_TICKER,
                                                        class_code=market, id=ticker)
        # .shares(instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE)
        # for instrument in instruments.instruments:
        #     print(f"{instrument.name=}, {instrument.class_code=}")
        price = await client.market_data.get_last_prices(figi=[instruments.instrument.figi])
        # market = await client.market_data.get_candles(figi=instruments.instrument.figi,
        #     instrument_id=instruments.instrument.uid,
        #     from_=now() - timedelta(days=1),
        #     interval=CandleInterval.CANDLE_INTERVAL_5_MIN,
        #     candle_source_type=CandleSource.CANDLE_SOURCE_UNSPECIFIED,
        #                                               )
        nano = str(price.last_prices[0].price.nano)
        units = str(price.last_prices[0].price.units)
        print(f"{units=}")
        k = False
        real_nano = ""
        for num in nano:
            if num == "0" and not k:
                continue
            elif num != "0" and not k:
                k = True
                real_nano += num
            elif num != "0":
                real_nano += num


        print(f"{nano=}; {real_nano=}")
        if real_nano != "":
            return units + "," + real_nano + " ₽"
        else:
            return units + " ₽"

@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    # Most event objects have aliases for API methods that can be called in events' context
    # For example if you want to answer to incoming message you can use `message.answer(...)` alias
    # and the target chat will be passed to :ref:`aiogram.methods.send_message.SendMessage`
    # method automatically or call API method directly via
    # Bot instance: `bot.send_message(chat_id=message.chat.id, ...)`
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!", reply_markup=StartKeyboard)




# @router.message()
# @user_id_middleware
# async def echo_handler(message: Message) -> None:
#     try:
#         # Send a copy of the received message
#         price = await get_current_price_by_ticker(str(message.text))
#         await message.answer(price)
#     except TypeError:
#         # But not all the types is supported to be copied so need to handle it
#         await message.answer("Nice try!")


@router.message(F.text == "Создать уведомление")
async def create_notification_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(CreateNotification.ticker)
    await message.answer("Введите тикер акции, которая торгуется на мосбирже. Например: HEAD")

@router.message(CreateNotification.ticker)
async def ticker_handler(message: Message, state: FSMContext) -> None:
    await state.update_data(ticker=message.text)
    await state.set_state(CreateNotification.price)
    await message.answer("Введите целевую цену акции в рублях. Например: 5100,5")

@router.message(CreateNotification.price)
async def ticker_handler(message: Message, state: FSMContext) -> None:
    await state.update_data(price=message.text)
    data = await state.get_data()
    await message.answer(f"{data["ticker"]=}, {data["price"]=}", reply_markup=StartKeyboard)
    await state.clear()