from functools import wraps
from typing import Callable


from app.utils.unitofwork import UnitOfWork
from app.services.notification_service import NotificationService




def with_notification_service(func: Callable):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        nt_service = NotificationService(UnitOfWork())
        return await func(nt_service, *args, **kwargs)

    return wrapper


