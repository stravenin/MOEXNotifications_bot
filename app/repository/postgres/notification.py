from typing import List

from sqlalchemy import select, distinct

from app.core.schemas import Notification
from app.models.notification import NotificationModel
from app.repository.base_repository import SqlRepository


class NotificationRepository(SqlRepository):
    async def create_notification(self, raw: NotificationModel) -> NotificationModel:
        self.session.add(raw)
        await self.session.flush()

        return raw

    async def get_notifications_by_user_id(self, user_id: int) -> List[NotificationModel]:
        raw = await self.session.execute(select(NotificationModel).where(NotificationModel.user_id == user_id))

        return raw.scalars().all() or []

    async def get_notification_by_id(self, _id: int) -> NotificationModel | None:
        raw = await self.session.execute(select(NotificationModel).where(NotificationModel.id == _id))
        return raw.scalar_one_or_none()

    async def delete_notification_by_id(self, _id: int) -> bool:
        nt = await self.get_notification_by_id(_id)
        if not nt:
            return False
        await self.session.delete(nt)
        await self.session.commit()
        return True

    async def get_all_notifications(self) -> List[Notification]:
        raw = await self.session.execute(select(NotificationModel))

        return raw.scalars().all() or []

    async def get_all_user_ids(self) -> List[int]:
        raw = await self.session.execute(select(distinct(NotificationModel.user_id)))
        return raw.scalars().all() or []