from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.notifications import NotificationNotFoundException
from models import NotificationLog, NotificationType
from repositories.notifications import NotificationRepository
from services.email import send_email
from services.notification_templates import get_subject, render_template


class NotificationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = NotificationRepository(session)

    async def register_notification(
        self,
        recipient_email: str,
        notification_type: NotificationType,
        context: dict,
    ) -> NotificationLog:
        subject = get_subject(notification_type)
        log = await self.repository.create(
            recipient_email=recipient_email,
            notification_type=notification_type,
            subject=subject,
            context=context,
        )
        await self.session.commit()
        await self.session.refresh(log)
        return log

    async def deliver(self, notification_id: int) -> None:
        log = await self.repository.get_by_id(notification_id)
        if log is None:
            raise NotificationNotFoundException(
                f"Notification with id={notification_id} was not found"
            )
        html_body = render_template(log.notification_type, log.context)
        await send_email(
            to=log.recipient_email, subject=log.subject, html_body=html_body
        )
        await self.repository.mark_sent(notification_id)
        await self.session.commit()

    async def mark_failed(
        self, notification_id: int, error_message: str
    ) -> None:
        await self.repository.mark_failed(notification_id, error_message)
        await self.session.commit()

    async def get_log(self, notification_id: int) -> NotificationLog:
        log = await self.repository.get_by_id(notification_id)
        if log is None:
            raise NotificationNotFoundException(
                f"Notification with id={notification_id} was not found"
            )
        return log

    async def list_logs(self, **filters) -> list[NotificationLog]:
        return await self.repository.list_logs(**filters)

    async def purge_old_logs(self, days: int) -> int:
        deleted = await self.repository.delete_older_than(days)
        await self.session.commit()
        return deleted
