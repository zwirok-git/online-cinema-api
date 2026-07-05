from exceptions.auth import (
    GroupDoesNotExist,
    InvalidCredentials,
    PermissionDenied,
    UserAlreadyExists,
    UserDoesNotExists,
    UserNotActivated,
)
from models.users import UserGroupEnum, UserModel
from repositories.users import GroupRepository, UserRepository
from security.passwords import get_password_hash, verify_password


class UserService:
    def __init__(
        self,
        user_repository: UserRepository,
        group_repository: GroupRepository,
    ) -> None:
        self.user_repository = user_repository
        self.group_repository = group_repository

    async def create_user(self, email: str, raw_password: str) -> UserModel:
        existing_user = await self.user_repository.get_by_email(email)
        if existing_user is not None:
            raise UserAlreadyExists("User with this email already exists")

        hashed_password = get_password_hash(password=raw_password)
        group = await self.group_repository.get_group_by_name(
            UserGroupEnum.USER
        )
        if group is None:
            raise GroupDoesNotExist("Group with this email already exists")

        user = UserModel(
            email=email,
            hashed_password=hashed_password,
            group=group,
        )
        await self.user_repository.create(user)
        return user

    async def get_user_by_id(self, user_id: int) -> UserModel:
        user = await self.user_repository.get_by_id(user_id)
        if user is None:
            raise UserDoesNotExists("User with this id does not exist")
        return user

    async def get_user_by_email(self, email: str) -> UserModel:
        user = await self.user_repository.get_by_email(email)
        if user is None:
            raise UserDoesNotExists("User with this email does not exist")
        return user

    async def validate_credentials(
        self, email: str, password: str
    ) -> UserModel:
        user = await self.get_user_by_email(email)
        if not verify_password(password, user.hashed_password):
            raise InvalidCredentials("Credentials are invalid.")
        if not user.is_active:
            raise UserNotActivated("User is inactive.")
        return user

    async def change_password(
        self, user: UserModel, old_password: str, new_password: str
    ) -> UserModel:
        if not verify_password(old_password, user.hashed_password):
            raise InvalidCredentials("Old password is invalid.")

        user.hashed_password = get_password_hash(password=new_password)
        await self.user_repository.update(user)
        return user

    async def manually_activate_user(self, user_id: int) -> UserModel:
        user = await self.get_user_by_id(user_id)
        user.is_active = True
        await self.user_repository.update(user)
        return user

    async def set_user_group(
        self, user_id: int, group: UserGroupEnum
    ) -> UserModel:
        user = await self.get_user_by_id(user_id)
        group_model = await self.group_repository.get_group_by_name(group)
        if group_model is None:
            raise GroupDoesNotExist("Group does not exist")

        user.group = group_model
        await self.user_repository.update(user)
        return user

    @staticmethod
    def ensure_user_has_role(
        user: UserModel, allowed_roles: tuple[UserGroupEnum, ...]
    ) -> None:
        if user.group.name not in allowed_roles:
            raise PermissionDenied("You do not have permission.")
