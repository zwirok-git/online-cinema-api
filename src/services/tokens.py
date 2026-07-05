import secrets
from datetime import datetime, timedelta, timezone

from core.config import settings
from exceptions.auth import (
    TokenAlreadyExists,
    TokenExpired,
    TokenInvalid,
    TokenNotExists,
    UserAlreadyActivated,
    UserNotActivated,
)
from models.tokens import (
    ActivationTokenModel,
    PasswordResetTokenModel,
    RefreshTokenModel,
)
from models.users import UserModel
from repositories.tokens import TokenRepository
from security.jwt_tokens import JWTService
from security.passwords import get_password_hash


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

    async def resend_activation_token(
        self, user: UserModel
    ) -> ActivationTokenModel:
        if user.is_active:
            raise UserAlreadyActivated("User is already activated.")

        exists_token = (
            await self.token_repository.get_activation_token_by_user_id(
                user_id=user.id
            )
        )

        if exists_token is not None:
            if exists_token.expires_at > datetime.now(timezone.utc):
                raise TokenAlreadyExists(
                    "Token already exists. Check your email."
                )
            await self.token_repository.delete_activation_token(exists_token)

        return await self.create_activation_token(user_id=user.id)

    async def create_refresh_token(self, user_id: int) -> RefreshTokenModel:
        jwt_service = JWTService()
        refresh_token_value = jwt_service.create_refresh_token(
            data={"user_id": user_id}
        )
        refresh_token = RefreshTokenModel(
            user_id=user_id,
            token=refresh_token_value,
            expires_at=datetime.now(timezone.utc)
            + settings.REFRESH_TOKEN_EXPIRE,
        )
        await self.token_repository.create_refresh_token(refresh_token)
        return refresh_token

    async def refresh_access_token(self, token_value: str) -> str:
        jwt_service = JWTService()
        payload = jwt_service.decode_token(token_value)

        if payload.get("type") != "refresh":
            raise TokenInvalid("Invalid token type.")

        refresh_token = await self.token_repository.get_refresh_token(
            token_value
        )
        if refresh_token is None:
            raise TokenNotExists("Refresh token does not exist.")

        if refresh_token.expires_at < datetime.now(timezone.utc):
            await self.token_repository.delete_refresh_token(refresh_token)
            raise TokenExpired("Refresh token expired.")

        return jwt_service.create_access_token(
            data={"user_id": refresh_token.user_id}
        )

    async def revoke_refresh_token(self, token_value: str) -> None:
        refresh_token = await self.token_repository.get_refresh_token(
            token_value
        )
        if refresh_token is None:
            raise TokenNotExists("Refresh token does not exist.")

        await self.token_repository.delete_refresh_token(refresh_token)

    async def create_password_reset_token(
        self, user: UserModel
    ) -> PasswordResetTokenModel:
        if not user.is_active:
            raise UserNotActivated("User is inactive.")

        exists_token = (
            await self.token_repository.get_password_reset_token_by_user_id(
                user_id=user.id
            )
        )
        if exists_token is not None:
            await self.token_repository.delete_password_reset_token(
                exists_token
            )

        token = PasswordResetTokenModel(
            token=secrets.token_urlsafe(32),
            user_id=user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )
        await self.token_repository.create_password_reset_token(token)
        return token

    async def reset_password(
        self, token_value: str, new_password: str
    ) -> UserModel:
        token = await self.token_repository.get_password_reset_token(
            token_value
        )

        if token is None:
            raise TokenInvalid("Invalid token.")

        if token.expires_at < datetime.now(timezone.utc):
            await self.token_repository.delete_password_reset_token(token)
            raise TokenExpired("Token expired.")

        token.user.hashed_password = get_password_hash(password=new_password)
        await self.token_repository.delete_password_reset_token(token)
        await self.token_repository.delete_user_refresh_tokens(token.user_id)
        return token.user

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
