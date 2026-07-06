from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.tokens import (
    ActivationTokenModel,
    PasswordResetTokenModel,
    RefreshTokenModel,
)


class TokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_activation_token(
        self, token: ActivationTokenModel
    ) -> ActivationTokenModel:
        self.session.add(token)
        await self.session.flush()
        return token

    async def get_activation_token_by_token(
        self, token_value: str
    ) -> ActivationTokenModel | None:
        stmt = select(ActivationTokenModel).where(
            ActivationTokenModel.token == token_value
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_activation_token_by_user_id(
        self, user_id: int
    ) -> ActivationTokenModel | None:
        stmt = select(ActivationTokenModel).where(
            ActivationTokenModel.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_activation_token(
        self, token: ActivationTokenModel
    ) -> None:
        await self.session.delete(token)
        await self.session.flush()

    async def delete_expired_activation_tokens(self, now: datetime):
        stmt = delete(ActivationTokenModel).where(
            ActivationTokenModel.expires_at < now
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def create_password_reset_token(
        self, token: PasswordResetTokenModel
    ) -> PasswordResetTokenModel:
        self.session.add(token)
        await self.session.flush()
        return token

    async def get_password_reset_token_by_token(
        self, token_value: str
    ) -> PasswordResetTokenModel | None:
        stmt = select(PasswordResetTokenModel).where(
            PasswordResetTokenModel.token == token_value
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_password_reset_token_by_user_id(
        self, user_id: int
    ) -> PasswordResetTokenModel | None:
        stmt = select(PasswordResetTokenModel).where(
            PasswordResetTokenModel.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_password_reset_token(
        self, token: PasswordResetTokenModel
    ) -> None:
        if token:
            await self.session.delete(token)
        await self.session.flush()

    async def delete_expired_password_reset_tokens(
        self, now: datetime
    ) -> None:
        stmt = delete(PasswordResetTokenModel).where(
            PasswordResetTokenModel.expires_at < now
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def create_refresh_token(
        self, token: RefreshTokenModel
    ) -> RefreshTokenModel:
        self.session.add(token)
        await self.session.flush()
        return token

    async def get_refresh_token_by_token(
        self, token_value: str
    ) -> RefreshTokenModel | None:
        stmt = select(RefreshTokenModel).where(
            RefreshTokenModel.token == token_value
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_refresh_token_by_user_id(
        self, user_id: int
    ) -> RefreshTokenModel | None:
        stmt = select(RefreshTokenModel).where(
            RefreshTokenModel.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_refresh_token(self, token: RefreshTokenModel) -> None:
        await self.session.delete(token)
        await self.session.flush()

    async def delete_expired_refresh_tokens(self, now: datetime) -> None:
        stmt = delete(RefreshTokenModel).where(
            RefreshTokenModel.expires_at < now
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def delete_users_refresh_tokens(self, user_id: int) -> None:
        stmt = delete(RefreshTokenModel).where(
            RefreshTokenModel.user_id == user_id
        )
        await self.session.execute(stmt)
        await self.session.flush()
