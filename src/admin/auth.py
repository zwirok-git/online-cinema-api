from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from starlette.requests import Request

from core.database import AsyncSessionLocal
from models.users import UserGroupEnum, UserModel
from security.passwords import verify_password


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        email = form.get("username")
        password = form.get("password")

        if not email or not password:
            return False

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(UserModel)
                .options(selectinload(UserModel.group))
                .where(UserModel.email == email)
            )
            user = result.scalar_one_or_none()

        if user is None:
            return False

        if not user.is_active:
            return False

        if not verify_password(password, user.hashed_password):
            return False

        if user.group.name not in (
            UserGroupEnum.ADMIN,
            UserGroupEnum.MODERATOR,
        ):
            return False

        request.session.update(
            {
                "admin_user_id": user.id,
                "admin_group": user.group.name.value,
            }
        )
        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return request.session.get("admin_user_id") is not None
