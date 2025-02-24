import asyncio
from datetime import datetime
import aiocron

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
async def foo(param):
    print(datetime.now().time(), param)

cron_min = aiocron.crontab('*/1 * * * *', func=foo, args=("At every minute",), start=True, loop=loop)
cron_hour = aiocron.crontab('0 */1 * * *', func=foo, args=("At minute 0 past every hour.",), start=True, loop=loop)
cron_day = aiocron.crontab('0 9 */1 * *', func=foo, args=("At 09:00 on every day-of-month",), start=True, loop=loop)
cron_week = aiocron.crontab('0 9 * * Mon', func=foo, args=("At 09:00 on every Monday",), start=True, loop=loop)

async def main():
    while True:
        await asyncio.sleep(1)


loop.run_until_complete(main())