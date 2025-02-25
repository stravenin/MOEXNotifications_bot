import asyncio
import logging
import sys


import aiocron
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.handlers import router, check_prices
from config import TG_TOKEN




loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)


dp = Dispatcher()







async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=TG_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp.include_router(router)
    cron_min = aiocron.crontab('*/1 * * * *', func=check_prices, args=[bot], start=True, loop=loop)

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    loop.run_until_complete(main())