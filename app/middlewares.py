import logging
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message

from app.core.config import THRUST_USERS


class AuthMiddleware(BaseMiddleware):
    async def __call__(self,
                       handler: Callable[[TelegramObject, Dict[str,Any]], Awaitable[Any]],
                       event: Message,
                       data: Dict[str, Any]) -> Any:
        chat_id = event.chat.id
        user_id = event.from_user.id
        
        logging.log(level=logging.INFO, msg=f"middleware {event.chat.id=}, {event.from_user.id=}")

        if user_id in THRUST_USERS and chat_id in THRUST_USERS:
            result = await handler(event, data)

            return result
        else:
            pass
