import logging

from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram import html, Router, F, Bot
from aiogram.fsm.state import State, StatesGroup


from tinkoff.invest import AsyncClient, CandleInterval
from tinkoff.invest.constants import INVEST_GRPC_API, INVEST_GRPC_API_SANDBOX
from tinkoff.invest.schemas import CandleSource, InstrumentIdType, InstrumentStatus

from app.core.db import db
from app.core.schemas import Notification
from app.keyboards import StartKeyboard
from app.middlewares import AuthMiddleware
from config import T_TOKEN, THRUST_USERS

router = Router()

router.message.outer_middleware(AuthMiddleware())

class CreateNotification(StatesGroup):
    ticker = State()
    target_price = State()




def get_real_nano(nano: str) -> str:
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

    return real_nano if real_nano != "" else "0"


async def get_current_price_by_figi(figi: list[str]) -> list[str]:
    async with (AsyncClient(T_TOKEN, target=INVEST_GRPC_API) as client):
        prices= []
        raw = await client.market_data.get_last_prices(figi=figi)
        print(f"{raw.last_prices=}")
        for price in raw.last_prices:
            nano = str(price.price.nano)
            units = str(price.price.units)
            print(f"{units=}")
            real_nano = get_real_nano(nano)
            prices.append(units + "." + real_nano)

        return prices

async def get_share_figi_by_ticker(ticker: str, market: str = "TQBR"):
    async with (AsyncClient(T_TOKEN, target=INVEST_GRPC_API) as client):
        instruments = await client.instruments.share_by(id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_TICKER,
                                                        class_code=market, id=ticker)
        # .shares(instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE)
        # for instrument in instruments.instruments:
        #     print(f"{instrument.name=}, {instrument.class_code=}")
        return instruments.instrument.figi

async def get_current_price_by_ticker(ticker: str) -> str:
    async with (AsyncClient(T_TOKEN, target=INVEST_GRPC_API) as client):
        figi = await get_share_figi_by_ticker(ticker)

        price = await client.market_data.get_last_prices(figi=[figi])

        nano = str(price.last_prices[0].price.nano)
        units = str(price.last_prices[0].price.units)
        print(f"{units=}")

        real_nano = get_real_nano(nano)

        return units + "." + real_nano


async def new_notification(data: dict[str, str], user_id: int) -> float | None:
    ticker = data["ticker"]
    target_price = data["target_price"]

    if 0 == len(ticker) or len(ticker) > 4 or len(target_price) == 0:
        raise ValueError("Введите корректный тикер и цену")
    try:
        target_price = target_price.replace(" ", "").replace(",",".")
        float(target_price)
    except:
        raise ValueError("Введите целевую цену в форме десятичной дроби")

    figi = await get_share_figi_by_ticker(ticker)
    print(f"{figi=}")
    price = await get_current_price_by_figi([figi])
    print(f"{price=}")

    nt = Notification(
        user_id=user_id,
        ticker=ticker,
        target_price=target_price,
        price=price[0],
        figi=figi
    )

    response = await db.add_notification(nt)
    change_percent = (float(nt.target_price) - float(nt.price)) / float(nt.price) * 100

    return change_percent if response else None


async def check_prices(bot: Bot):
    logging.log(level=logging.INFO, msg="CRON")
    for user_id in THRUST_USERS:
        nts = await db.get_notifications_by_user_id(user_id)
        if not nts:
            return None
        nts_figi = [nt.figi for nt in nts]
        current_prices = await get_current_price_by_figi(nts_figi)

        for nt, current_price in zip(nts, current_prices):
            price_percent = (float(nt.target_price)-float(nt.price))/float(nt.price) * 100
            print(f"{price_percent=}, {current_price=}, {nt.target_price=}")
            if price_percent > 0 and float(current_price) >= float(nt.target_price):

                await bot.send_message(user_id,
                                       f"Акция {nt.ticker} достигла целевой цены: {nt.target_price}. Текущая цена: {current_price}. \n"
                                       f"Изменение составило: {str((float(current_price)-float(nt.price))/float(nt.price) * 100)}")
                await db.delete_notifications_by_id([nt.id])

            if price_percent < 0 and float(current_price) <= float(nt.target_price):

                await bot.send_message(user_id,
                                       f"Акция {nt.ticker} достигла целевой цены: {nt.target_price}. Текущая цена: {current_price}")
                await db.delete_notifications_by_id([nt.id])




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
    await state.set_state(CreateNotification.target_price)
    await message.answer("Введите целевую цену акции в рублях. Например: 5100,5")

@router.message(CreateNotification.target_price)
async def ticker_handler(message: Message, state: FSMContext) -> None:
    await state.update_data(target_price=message.text)
    data = await state.get_data()

    try:
        new_nt = await new_notification(data, message.from_user.id)

    except ValueError as e:
        new_nt = None
        await message.answer(
            f"Ошибка при вводе данных: {e.args[0] if len(e.args) > 0 else e.args}.",
            reply_markup=StartKeyboard)

    except Exception as e:
        new_nt = None
        await message.answer(
            f"Ошибка создания уведомления: {e.args[0] if len(e.args) > 0 else e.args}.",
            reply_markup=StartKeyboard)

    if new_nt:
        await message.answer(f"Уведомление для {data["ticker"]} с целевой ценой: {data["target_price"]}р успешно создано. Изменение: {round(new_nt, 1)}%", reply_markup=StartKeyboard)

    await state.clear()