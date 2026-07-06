from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.users import (
    UserGroupModel,
    UserModel,
    UserProfileModel,
)


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(
        self, user_id: int, with_relations: bool = False
    ) -> UserModel | None:
        stmt = select(UserModel).where(UserModel.id == user_id)
        if with_relations:
            stmt = stmt.options(
                selectinload(UserModel.group), selectinload(UserModel.profile)
            )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(
        self, user_email: str, with_relations: bool = False
    ) -> UserModel | None:
        stmt = select(UserModel).where(UserModel.email == user_email)
        if with_relations:
            stmt = stmt.options(
                selectinload(UserModel.group), selectinload(UserModel.profile)
            )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, limit: int, offset: int) -> Sequence[UserModel]:
        stmt = (
            select(UserModel)
            .options(
                selectinload(UserModel.group), selectinload(UserModel.profile)
            )
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

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

    async def create_profile(
        self, profile: UserProfileModel
    ) -> UserProfileModel:
        self.session.add(profile)
        await self.session.flush()
        await self.session.refresh(profile)
        return profile

    async def get_total_users(self) -> int:
        stmt = select(func.count(UserModel.id))
        result = await self.session.execute(stmt)
        return result.scalar() or 0


class GroupRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_group_by_name(
        self, group_name: str
    ) -> UserGroupModel | None:
        stmt = select(UserGroupModel).where(UserGroupModel.name == group_name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_group_by_id(self, group_id: int) -> UserGroupModel | None:
        stmt = select(UserGroupModel).where(UserGroupModel.id == group_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self) -> Sequence[UserGroupModel]:
        stmt = select(UserGroupModel)
        result = await self.session.execute(stmt)
        return result.scalars().all()
