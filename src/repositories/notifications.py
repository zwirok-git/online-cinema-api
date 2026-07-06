from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import NotificationLog, NotificationStatus, NotificationType


class NotificationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        recipient_email: str,
        notification_type: NotificationType,
        subject: str,
        context: dict,
    ) -> NotificationLog:
        log = NotificationLog(
            recipient_email=recipient_email,
            notification_type=notification_type,
            subject=subject,
            context=context,
            status=NotificationStatus.PENDING,
        )
        self.session.add(log)
        await self.session.flush()
        await self.session.refresh(log)
        return log

    async def get_by_id(self, notification_id: int) -> NotificationLog | None:
        query = select(NotificationLog).where(
            NotificationLog.id == notification_id
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def mark_sent(self, notification_id: int) -> None:
        log = await self.get_by_id(notification_id)
        if log is None:
            return
        log.status = NotificationStatus.SENT
        log.sent_at = datetime.now(timezone.utc)
        log.attempts += 1
        await self.session.flush()

    async def mark_failed(
        self, notification_id: int, error_message: str
    ) -> None:
        log = await self.get_by_id(notification_id)
        if log is None:
            return
        log.status = NotificationStatus.FAILED
        log.error_message = error_message
        log.attempts += 1
        await self.session.flush()

    async def list_logs(
        self,
        recipient_email: str | None = None,
        notification_type: NotificationType | None = None,
        status: NotificationStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[NotificationLog]:
        query = select(NotificationLog).order_by(
            NotificationLog.created_at.desc()
        )
        if recipient_email:
            query = query.where(
                NotificationLog.recipient_email == recipient_email
            )
        if notification_type:
            query = query.where(
                NotificationLog.notification_type == notification_type
            )
        if status:
            query = query.where(NotificationLog.status == status)
        query = query.limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def delete_older_than(self, days: int) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        result = await self.session.execute(
            delete(NotificationLog).where(
                NotificationLog.created_at < cutoff
            )
        )
        rowcount = getattr(result, "rowcount", None)
        if isinstance(rowcount, int):
            return rowcount
        return 0
