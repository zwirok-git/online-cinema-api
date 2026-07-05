import secrets
from datetime import datetime, timedelta, timezone

from exceptions.auth import (
    TokenAlreadyExists,
    TokenExpired,
    TokenInvalid,
)
from models.tokens import ActivationTokenModel
from models.users import UserModel
from repositories.tokens import TokenRepository


class TokenService:
    def __init__(self, token_repository: TokenRepository) -> None:
        self.token_repository = token_repository

    async def create_activation_token(
        self, user_id: int
    ) -> ActivationTokenModel:
        exists_token = (
            await self.token_repository.get_activation_token_by_user_id(
                user_id=user_id
            )
        )
        if exists_token is not None:
            raise TokenAlreadyExists("Token already exists. Check your email.")

        token = ActivationTokenModel(
            token=secrets.token_urlsafe(32),
            user_id=user_id,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )
        await self.token_repository.create_activation_token(token)
        return token

    async def activate_user(self, token_value: str) -> UserModel:
        token = await self.token_repository.get_activation_token(token_value)

        if token is None:
            raise TokenInvalid("Invalid token.")

        if token.expires_at < datetime.now(timezone.utc):
            await self.token_repository.delete_activation_token(token)
            raise TokenExpired("Token expired.")

        token.user.is_active = True
        await self.token_repository.delete_activation_token(token)
        return token.user
