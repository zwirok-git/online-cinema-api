from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.users import UserGroupEnum, UserGroupModel, UserModel


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


class GroupRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_group_by_name(
        self, name: UserGroupEnum
    ) -> UserGroupModel | None:
        stmt = select(UserGroupModel).where(UserGroupModel.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_group_by_id(self, group_id: int) -> UserGroupModel | None:
        stmt = select(UserGroupModel).where(UserGroupModel.id == group_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self) -> list[UserGroupModel]:
        stmt = select(UserGroupModel)
        result = await self.session.execute(stmt)
        return result.scalars().all()
