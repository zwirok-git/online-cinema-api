import secrets
from datetime import datetime, timedelta, timezone

from core.config import settings
from exceptions.auth import TokenAlreadyExpired, TokenDoesNotExists
from models import PasswordResetTokenModel, RefreshTokenModel
from models.tokens import ActivationTokenModel
from repositories.tokens import TokenRepository


class TokenService:
    def __init__(self, token_repository: TokenRepository) -> None:
        self.token_repository = token_repository

    async def get_activation_token_by_token(
        self, token_value: str
    ) -> ActivationTokenModel | None:
        token = await self.token_repository.get_activation_token_by_token(
            token_value=token_value
        )
        if token is None:
            raise TokenDoesNotExists("Activation token does not exist.")
        if token.expires_at < datetime.now(timezone.utc):
            raise TokenAlreadyExpired("Activation token has already expired.")
        return token

    async def get_activation_token_by_user_id(
        self, user_id: int
    ) -> ActivationTokenModel | None:
        token = await self.token_repository.get_activation_token_by_user_id(
            user_id
        )
        return token

    async def create_activation_token(
        self, user_id: int
    ) -> ActivationTokenModel:
        activation_token = ActivationTokenModel(
            token=secrets.token_urlsafe(32),
            user_id=user_id,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )
        await self.token_repository.create_activation_token(
            token=activation_token
        )
        return activation_token

    async def delete_activation_token(
        self, token: ActivationTokenModel
    ) -> None:
        await self.token_repository.delete_activation_token(token)

    async def get_reset_token_by_token(
        self, token_value: str
    ) -> PasswordResetTokenModel | None:
        token = await self.token_repository.get_password_reset_token_by_token(
            token_value=token_value
        )
        if token is None:
            raise TokenDoesNotExists("Token with this value does not exist.")
        if token.expires_at < datetime.now(timezone.utc):
            raise TokenAlreadyExpired("Token has already expired.")
        return token

    async def get_reset_token_by_user_id(
        self, user_id: int
    ) -> PasswordResetTokenModel | None:
        token = (
            await self.token_repository.get_password_reset_token_by_user_id(
                user_id=user_id
            )
        )
        return token

    async def create_reset_token(
        self, user_id: int
    ) -> PasswordResetTokenModel:
        reset_token = PasswordResetTokenModel(
            token=secrets.token_urlsafe(32),
            user_id=user_id,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )
        await self.token_repository.create_password_reset_token(
            token=reset_token
        )
        return reset_token

    async def delete_reset_token(self, token: ActivationTokenModel) -> None:
        await self.token_repository.delete_password_reset_token(token)

    async def get_refresh_token_by_token(
        self, token_value: str
    ) -> RefreshTokenModel | None:
        token = await self.token_repository.get_refresh_token_by_token(
            token_value=token_value
        )
        if token is None:
            raise TokenDoesNotExists("Token with this value does not exist.")
        if token.expires_at < datetime.now(timezone.utc):
            raise TokenAlreadyExpired("Token has already expired.")
        return token

    async def create_refresh_token(
        self, token_value: str, user_id: int
    ) -> RefreshTokenModel:
        refresh_token = RefreshTokenModel(
            user_id=user_id,
            expires_at=datetime.now(timezone.utc)
            + settings.REFRESH_TOKEN_EXPIRE,
            token=token_value,
        )
        await self.token_repository.create_refresh_token(token=refresh_token)
        return refresh_token

    async def delete_refresh_token(self, token_value: int) -> None:
        token = await self.token_repository.get_refresh_token_by_token(
            token_value=token_value
        )
        await self.token_repository.delete_refresh_token(token=token)

    async def delete_all_refresh_tokens(self, user_id: int) -> None:
        await self.token_repository.delete_users_refresh_tokens(
            user_id=user_id
        )
