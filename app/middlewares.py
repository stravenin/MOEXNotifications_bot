import logging
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message

from app.services.notification_service import NotificationService
from app.utils.unitofwork import UnitOfWork


class DepMiddleware(BaseMiddleware):
    async def __call__(self,
                       handler: Callable[[TelegramObject, Dict[str,Any]], Awaitable[Any]],
                       event: Message,
                       data: Dict[str, Any]) -> Any:

        
        logging.log(level=logging.INFO, msg=f"DEP_middleware {event.from_user.id=}")
        nt_service = NotificationService(UnitOfWork())
        data["nt_service"] = nt_service
        result = await handler(event, data)

        return result
