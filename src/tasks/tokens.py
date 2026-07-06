import asyncio
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from core.celery import celery
from core.config import settings
from repositories.tokens import TokenRepository


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
