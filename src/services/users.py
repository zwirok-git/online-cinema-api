from pathlib import Path
from typing import Sequence
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from exceptions.auth import (
    GroupDoesNotExist,
    InvalidCredentials,
    InvalidOldPassword,
    InvalidToken,
    UserAlreadyActivated,
    UserAlreadyExists,
    UserDoesNotExists,
    UserNotActivated,
)
from models import NotificationType
from models.users import UserModel, UserProfileModel
from repositories.users import GroupRepository, UserRepository
from security.passwords import get_password_hash, verify_password
from services.jwt_tokens import JWTService
from services.notification_templates import get_subject, render_template
from services.tokens import TokenService
from tasks.send_email import send_email_task


class UserService:
    def __init__(
        self,
        session: AsyncSession,
        user_repository: UserRepository,
        group_repository: GroupRepository,
        token_service: TokenService,
        jwt_service: JWTService,
    ) -> None:
        self.session = session
        self.user_repository = user_repository
        self.group_repository = group_repository
        self.token_service = token_service
        self.jwt_service = jwt_service

    async def exists_by_email(self, email: str) -> bool:
        user = await self.user_repository.get_by_email(email)
        return user is not None

    async def get_user_by_id(
        self, user_id: int, with_relations: bool = False
    ) -> UserModel:
        user = await self.user_repository.get_by_id(
            user_id, with_relations=with_relations
        )
        if user is None:
            raise UserDoesNotExists("User with this id does not exist.")
        return user

    async def register_user(self, email: str, raw_password: str) -> UserModel:
        existing_user = await self.exists_by_email(email=email)
        if existing_user:
            raise UserAlreadyExists("User with this email already exists.")

        hashed_password = get_password_hash(password=raw_password)
        group = await self.group_repository.get_group_by_name("user")
        if group is None:
            raise GroupDoesNotExist("Default user group with does not exists.")

        user = UserModel(
            email=email,
            hashed_password=hashed_password,
            group=group,
        )
        await self.user_repository.create(user)
        profile = UserProfileModel(user_id=user.id)
        await self.user_repository.create_profile(profile=profile)
        activation_token = await self.token_service.create_activation_token(
            user_id=user.id
        )
        activations_link = (
            f"{settings.BASE_URL}/users/activate"
            f"?activation_token={activation_token.token}"
        )

        send_email_task.delay(
            to=user.email,
            subject=get_subject(notification_type=NotificationType.ACTIVATION),
            html_body=render_template(
                notification_type=NotificationType.ACTIVATION,
                context={"activation_link": activations_link},
            ),
        )

        await self.session.commit()
        return user

    async def resend_activation_token(self, email: str) -> None:
        user = await self.user_repository.get_by_email(user_email=email)
        if user is None:
            raise UserDoesNotExists("User with this email does not exist.")
        if user.is_active:
            raise UserAlreadyActivated("User already activated.")

        existing_token = (
            await self.token_service.get_activation_token_by_user_id(
                user_id=user.id
            )
        )
        if existing_token is not None:
            await self.token_service.delete_activation_token(
                token=existing_token
            )
        activation_token = await self.token_service.create_activation_token(
            user_id=user.id
        )
        activations_link = (
            f"{settings.BASE_URL}/users/activate"
            f"?activation_token={activation_token.token}"
        )

        send_email_task.delay(
            to=user.email,
            subject=get_subject(
                notification_type=NotificationType.RESEND_ACTIVATION
            ),
            html_body=render_template(
                notification_type=NotificationType.RESEND_ACTIVATION,
                context={"activation_link": activations_link},
            ),
        )

        await self.session.commit()

    async def activate_user(self, token: str) -> UserModel:
        token_model = await self.token_service.get_activation_token_by_token(
            token_value=token
        )

        user_model = await self.user_repository.get_by_id(
            user_id=token_model.user_id
        )
        if user_model is None:
            raise UserDoesNotExists("User does not exist.")

        user_model.is_active = True
        await self.token_service.delete_activation_token(token_model)
        await self.session.commit()
        return user_model

    async def login_user(self, email: str, password: str) -> tuple[str, str]:
        user = await self.user_repository.get_by_email(user_email=email)

        if user is None or not verify_password(password, user.hashed_password):
            raise InvalidCredentials("Invalid email or password")
        if not user.is_active:
            raise UserNotActivated("Account exists but is not activated yet.")

        refresh_token = self.jwt_service.create_refresh_token(
            data={"user_id": user.id}
        )
        await self.token_service.create_refresh_token(
            token_value=refresh_token,
            user_id=user.id,
        )
        access_token = self.jwt_service.create_access_token(
            data={"user_id": user.id}
        )
        await self.session.commit()
        return refresh_token, access_token

    async def logout_user(self, user_id: int) -> None:
        await self.token_service.delete_all_refresh_tokens(user_id=user_id)
        await self.session.commit()

    async def refresh_access_token(
        self, refresh_token: str
    ) -> tuple[str, str]:
        decoded_refresh_token_data = self.jwt_service.decode_token(
            token=refresh_token
        )
        if decoded_refresh_token_data.get("type") != "refresh":
            raise InvalidToken("Not a refresh token.")

        token = await self.token_service.get_refresh_token_by_token(
            refresh_token
        )
        if token is None:
            raise InvalidToken("Invalid refresh token.")
        user_id = token.user_id
        await self.token_service.delete_refresh_token(
            token_value=refresh_token
        )

        refresh_token = self.jwt_service.create_refresh_token(
            data={"user_id": user_id}
        )
        await self.token_service.create_refresh_token(
            token_value=refresh_token,
            user_id=user_id,
        )
        access_token = self.jwt_service.create_access_token(
            data={"user_id": user_id}
        )
        await self.session.commit()
        return refresh_token, access_token

    async def change_password(
        self, user: UserModel, new_password: str, old_password: str
    ) -> None:
        if not verify_password(old_password, user.hashed_password):
            raise InvalidOldPassword("Invalid old password.")

        user.hashed_password = get_password_hash(new_password)
        await self.token_service.delete_all_refresh_tokens(user_id=user.id)
        await self.session.commit()

    async def reset_password(self, user_email: str):
        user = await self.user_repository.get_by_email(user_email=user_email)
        if user is None:
            raise UserDoesNotExists("User does not exist.")

        existing_token = await self.token_service.get_reset_token_by_user_id(
            user_id=user.id
        )
        if existing_token is not None:
            await self.token_service.delete_reset_token(token=existing_token)
        reset_token = await self.token_service.create_reset_token(
            user_id=user.id
        )
        reset_link = (
            f"{settings.BASE_URL}/users/reset/complete"
            f"?reset_token={reset_token.token}"
        )

        send_email_task.delay(
            to=user.email,
            subject=get_subject(
                notification_type=NotificationType.RESEND_ACTIVATION
            ),
            html_body=render_template(
                notification_type=NotificationType.RESEND_ACTIVATION,
                context={"reset_link": reset_link},
            ),
        )

        await self.session.commit()

    async def reset_password_complete(
        self, reset_token: str, new_password: str
    ) -> None:
        token = await self.token_service.get_reset_token_by_token(
            token_value=reset_token
        )
        if token is None:
            raise InvalidToken("Invalid password reset token.")
        user = await self.user_repository.get_by_id(user_id=token.user_id)
        if user is None:
            raise UserDoesNotExists("User does not exist.")

        user.hashed_password = get_password_hash(new_password)
        await self.token_service.delete_reset_token(token=token)
        await self.session.commit()

    async def get_me_profile(self, user: UserModel) -> UserModel:
        user_with_relations = await self.user_repository.get_by_email(
            user_email=user.email, with_relations=True
        )
        if user_with_relations is None:
            raise UserDoesNotExists("User does not exist.")
        return user

    async def change_profile(
        self, user: UserModel, profile_data: dict
    ) -> UserModel:
        user_with_relations = await self.user_repository.get_by_email(
            user_email=user.email, with_relations=True
        )
        if user_with_relations is None:
            raise UserDoesNotExists("User does not exist.")
        for key, value in profile_data.items():
            setattr(user_with_relations.profile, key, value)
        await self.session.commit()
        return user_with_relations

    async def get_all_users(
        self, limit: int = 10, offset: int = 0
    ) -> tuple[Sequence[UserModel], int]:
        total_user = await self.user_repository.get_total_users()

        users = await self.user_repository.get_all(
            limit=limit,
            offset=offset,
        )
        return users, int(total_user)

    async def change_group(self, user_id: int, group_name: str) -> UserModel:
        user_model = await self.user_repository.get_by_id(
            user_id, with_relations=True
        )
        if user_model is None:
            raise UserDoesNotExists("User with this id does not exists.")

        group = await self.group_repository.get_group_by_name(
            group_name=group_name
        )
        if group is None:
            raise GroupDoesNotExist("Group with this name does not exists.")

        user_model.group = group
        await self.session.commit()
        return user_model

    async def change_status(self, user_id: int) -> UserModel:
        user_model = await self.user_repository.get_by_id(
            user_id, with_relations=True
        )
        if user_model is None:
            raise UserDoesNotExists("User with this id does not exists.")
        user_model.is_active = True
        await self.session.commit()
        return user_model

    async def upload_avatar(
            self,
            user: UserModel,
            avatar: UploadFile,
    ) -> str:
        allowed_content_types = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
        }

        if avatar.content_type not in allowed_content_types:
            raise ValueError("Only jpeg, png and webp images are allowed.")

        content = await avatar.read()
        max_size = 2 * 1024 * 1024

        if len(content) > max_size:
            raise ValueError("Avatar size must be less than 2 MB.")

        user_with_relations = await self.user_repository.get_by_email(
            user_email=user.email,
            with_relations=True,
        )
        if user_with_relations is None:
            raise UserDoesNotExists("User does not exist.")

        extension = allowed_content_types[avatar.content_type]
        filename = f"{uuid4().hex}{extension}"

        avatars_dir = Path("media") / "avatars"
        avatars_dir.mkdir(parents=True, exist_ok=True)

        file_path = avatars_dir / filename
        file_path.write_bytes(content)

        avatar_url = f"{settings.BASE_URL}/media/avatars/{filename}"

        user_with_relations.profile.avatar = avatar_url
        await self.session.commit()

        return avatar_url
