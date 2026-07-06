import asyncio
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from core.celery import celery
from core.config import settings
from exceptions.notifications import EmailDeliveryException
from repositories.tokens import TokenRepository
from services.email import send_email


async def _delete_expired_tokens() -> None:
    engine = create_async_engine(settings.database_url)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_maker() as session:
            token_repository = TokenRepository(session)
            now = datetime.now(timezone.utc)
            await token_repository.delete_expired_refresh_tokens(now)
            await token_repository.delete_expired_activation_tokens(now)
            await token_repository.delete_expired_password_reset_tokens(now)
            await session.commit()
    finally:
        await engine.dispose()


@celery.task(name="delete_expired_tokens")
def delete_expired_tokens() -> str:
    asyncio.run(_delete_expired_tokens())
    return "Expired tokens cleaned up."


@celery.task(
    name="send_email_task",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def send_email_task(self, to: str, subject: str, html_body: str) -> str:
    try:
        send_email(to=to, subject=subject, html_body=html_body)
        return f"Email sent to {to}."
    except EmailDeliveryException as exc:
        raise self.retry(exc=exc) from exc
