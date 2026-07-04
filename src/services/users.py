from exceptions.auth import (
    GroupDoesNotExist,
    InvalidCredentials,
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
