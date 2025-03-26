import logging

from aiogram import Bot

from app.core.dependencies import with_notification_service
from app.services.notification_service import NotificationService


@with_notification_service
async def check_prices(nt_service: NotificationService, bot: Bot):

    logging.log(level=logging.INFO, msg="CRON")
    user_ids = await nt_service.get_all_user_ids()
    if not user_ids:
        return None
    for user_id in user_ids:
        nts = await nt_service.get_notifications_by_user_id(user_id)
        if not nts:
            return None

        for nt in nts:
            current_price = await nt_service.get_current_price_by_figi(nt.figi)

            price_percent = (float(nt.target_price)-float(nt.price))/float(nt.price) * 100
            real_price_percent = round(((float(current_price) - float(nt.price)) / float(nt.price) * 100), 1)
            print(f"{price_percent=}, {current_price=}, {nt.target_price=}")
            if price_percent > 0 and float(current_price) >= float(nt.target_price):


                await bot.send_message(user_id,
                                       f"🟢 Акция {nt.ticker} достигла целевой цены: {nt.target_price}. Текущая цена: {current_price}₽. \n"
                                       f"Изменение составило: {str(real_price_percent)}% от изначальной цены: {nt.price}₽")
                await nt_service.delete_notification_by_id(nt.id)

            if price_percent < 0 and float(current_price) <= float(nt.target_price):

                await bot.send_message(user_id,
                                       f"🔴 Акция {nt.ticker} достигла целевой цены: {nt.target_price}. Текущая цена: {current_price}₽. \n"
                                       f"Изменение составило: {str(real_price_percent)}% от изначальной цены: {nt.price}₽")
                await nt_service.delete_notification_by_id(nt.id)