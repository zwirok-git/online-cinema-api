from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.users import UserGroupEnum, UserGroupModel, UserModel


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: int) -> UserModel | None:
        stmt = (
            select(UserModel)
            .where(UserModel.id == user_id)
            .options(selectinload(UserModel.group))
        )
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        return user

    async def get_by_email(self, user_email: str) -> UserModel | None:
        stmt = (
            select(UserModel)
            .where(UserModel.email == user_email)
            .options(selectinload(UserModel.group))
        )
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        return user

    async def get_all(self, limit: int, offset: int) -> Sequence[UserModel]:
        stmt = (
            select(UserModel)
            .limit(limit)
            .offset(offset)
            .options(selectinload(UserModel.group))
        )
        result = await self.session.execute(stmt)
        users = result.scalars().all()
        return users

    async def create(self, user: UserModel) -> UserModel:
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def update(self, user: UserModel) -> UserModel:
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def delete(self, user: UserModel) -> None:
        await self.session.delete(user)
        await self.session.flush()


class GroupRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_group_by_name(
        self, group: UserGroupEnum
    ) -> UserGroupModel | None:
        stmt = select(UserGroupModel).where(UserGroupModel.name == group)
        result = await self.session.execute(stmt)
        group_model = result.scalars().first()
        return group_model
