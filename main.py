import asyncio
import logging
import sys
from datetime import datetime, timedelta
from functools import wraps
from typing import Callable

import aiocron
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from tinkoff.invest import AsyncClient, CandleInterval
from tinkoff.invest.constants import INVEST_GRPC_API, INVEST_GRPC_API_SANDBOX
from tinkoff.invest.schemas import CandleSource, InstrumentIdType, InstrumentStatus
from tinkoff.invest.utils import now

from config import TG_TOKEN, THRUST_USERS, T_TOKEN




loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)


dp = Dispatcher()


async def foo(bot: Bot):
    print(datetime.now().time())
    for chat_id in THRUST_USERS:
        await bot.send_message(chat_id, str(datetime.now().time()))



def user_id_middleware(func: Callable):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            chat_id = args[0].chat.id
            user_id = args[0].from_user.id
            print("middleware chat_id: ", chat_id)
            print("middleware.from_user.id: ", user_id)
            if user_id in THRUST_USERS and chat_id in THRUST_USERS:
                return await func(*args, **kwargs)
            else:
                pass
        except Exception as e:
            pass
    return wrapper

@dp.message(CommandStart())
@user_id_middleware
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    # Most event objects have aliases for API methods that can be called in events' context
    # For example if you want to answer to incoming message you can use `message.answer(...)` alias
    # and the target chat will be passed to :ref:`aiogram.methods.send_message.SendMessage`
    # method automatically or call API method directly via
    # Bot instance: `bot.send_message(chat_id=message.chat.id, ...)`
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!")


@dp.message((Command('head')))
@user_id_middleware
async def ticker_handler(message: Message) -> None:
    """
    Handler will forward receive a message back to the sender

    By default, message handler will handle all message types (like a text, photo, sticker etc.)
    """
    async with (AsyncClient(T_TOKEN, target=INVEST_GRPC_API) as client):
        instruments = await client.instruments.share_by(id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_TICKER,
                                                        class_code="TQBR", id="HEAD")
        # .shares(instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE)
        # for instrument in instruments.instruments:
        #     print(f"{instrument.name=}, {instrument.class_code=}")
        print(f"{instruments.instrument=}")
        print(f"{instruments.instrument.figi=}, {instruments.instrument.uid=}")
        price = await client.market_data.get_last_prices(instrument_id=instruments.instrument.uid)
        print(f"[x] {price.last_prices=}")
    await message.answer(instruments.instrument)

@dp.message()
@user_id_middleware
async def echo_handler(message: Message) -> None:
    """
    Handler will forward receive a message back to the sender

    By default, message handler will handle all message types (like a text, photo, sticker etc.)
    """
    try:
        # Send a copy of the received message
        await message.send_copy(chat_id=message.chat.id)
    except TypeError:
        # But not all the types is supported to be copied so need to handle it
        await message.answer("Nice try!")


async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=TG_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # cron_min = aiocron.crontab('*/1 * * * *', func=foo, args=[bot], start=True, loop=loop)

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    loop.run_until_complete(main())