import logging

from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram import html, Router, F, Bot
from aiogram.fsm.state import State, StatesGroup


from tinkoff.invest import AsyncClient
from tinkoff.invest.constants import INVEST_GRPC_API
from tinkoff.invest.schemas import InstrumentIdType

from app.core.db import db
from app.core.schemas import Notification
from app.keyboards import StartKeyboard, get_nts_inline, delete_nt_inline
from app.middlewares import AuthMiddleware
from app.core.config import T_TOKEN, THRUST_USERS

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


async def get_current_price_by_figi(figi: str) -> str:
    async with (AsyncClient(T_TOKEN, target=INVEST_GRPC_API) as client):
        raw = await client.market_data.get_last_prices(figi=[figi])

        print(f"{raw.last_prices=}")
        nano = str(raw.last_prices[0].price.nano)
        units = str(raw.last_prices[0].price.units)
        print(f"{units=}")
        real_nano = get_real_nano(nano)

        return units + "." + real_nano

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
    price = await get_current_price_by_figi(figi)
    print(f"{price=}")

    nt = Notification(
        user_id=user_id,
        ticker=ticker,
        target_price=target_price,
        price=price,
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

        for nt in nts:
            current_price = await get_current_price_by_figi(nt.figi)

            price_percent = (float(nt.target_price)-float(nt.price))/float(nt.price) * 100
            real_price_percent = round(((float(current_price) - float(nt.price)) / float(nt.price) * 100), 1)
            print(f"{price_percent=}, {current_price=}, {nt.target_price=}")
            if price_percent > 0 and float(current_price) >= float(nt.target_price):


                await bot.send_message(user_id,
                                       f"🟢 Акция {nt.ticker} достигла целевой цены: {nt.target_price}. Текущая цена: {current_price}. \n"
                                       f"Изменение составило: {str(real_price_percent)}% от изначальной цены: {}")
                await db.delete_notifications_by_id([nt.id])

            if price_percent < 0 and float(current_price) <= float(nt.target_price):

                await bot.send_message(user_id,
                                       f"🔴 Акция {nt.ticker} достигла целевой цены: {nt.target_price}. Текущая цена: {current_price}. \n"
                                       f"Изменение составило: {str(real_price_percent)}%")
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


@router.message(F.text == "Создать уведомление")
async def create_notification_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(CreateNotification.ticker)
    await message.answer("Введите тикер акции, которая торгуется на мосбирже. Например: HEAD")

@router.message(CreateNotification.ticker)
async def ticker_handler(message: Message, state: FSMContext) -> None:
    await state.update_data(ticker=message.text)
    await state.set_state(CreateNotification.target_price)
    price = await get_current_price_by_ticker(message.text)
    await message.answer(f"Введите целевую цену акции в рублях. Текущая: {price}")

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

@router.message(F.text == "Список уведомлений")
async def get_notifications_handler(message: Message) -> None:
    nts = await db.get_notifications_by_user_id(message.from_user.id)
    await message.answer("Список ваших уведомлений", reply_markup=get_nts_inline(nts))

@router.callback_query(F.data == "Back_to_nts")
async def back_to_nts_handler(call: CallbackQuery) -> None:
    nts = await db.get_notifications_by_user_id(call.from_user.id)
    await call.message.edit_text("Список ваших уведомлений", reply_markup=get_nts_inline(nts))

@router.callback_query(F.data == "Back_to_start")
async def back_start_handler(call: CallbackQuery) -> None:
    await call.message.delete()
    await call.message.answer(text="Выберите", reply_markup=StartKeyboard)

@router.callback_query(F.data.startswith("nt_"))
async def nt_id_handler(call: CallbackQuery) -> None:
    nt_id = int(call.data.replace("nt_",""))
    nt = await db.get_notification_by_id(nt_id)
    await call.message.edit_text("Нажмите на уведомление для удаления", reply_markup=delete_nt_inline(nt))

@router.callback_query(F.data.startswith("del_"))
async def nt_delete_handler(call: CallbackQuery) -> None:
    nt_id = int(call.data.replace("del_",""))
    await db.delete_notifications_by_id([nt_id])
    nts = await db.get_notifications_by_user_id(call.from_user.id)
    await call.message.edit_text("Список ваших уведомлений", reply_markup=get_nts_inline(nts))