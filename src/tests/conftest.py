import pytest
import pytest_asyncio
from fastapi import HTTPException, status
from typing import AsyncGenerator
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select

from main import app
from core.database import Base, get_db
from models.users import UserModel, UserGroupModel, UserGroupEnum
from api.dependencies import get_current_user, get_current_admin

TEST_DATABASE_URL = "postgresql+asyncpg://admin:some_password@online_cinema_db:5432/movies_test_db"


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with engine.connect() as connection:
        transaction = await connection.begin()
        async with AsyncSession(bind=connection, expire_on_commit=False) as session:
            for enum_item in UserGroupEnum:
                stmt = (
                    insert(UserGroupModel)
                    .values(name=enum_item)
                    .on_conflict_do_nothing(index_elements=['name'])
                )
                await session.execute(stmt)
            await session.flush()
            yield session
        await transaction.rollback()

    await engine.dispose()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def override_fastapi_db(db_session: AsyncSession):
    async def _override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> UserModel:
    result = await db_session.execute(
        select(UserGroupModel).where(UserGroupModel.name == UserGroupEnum.USER)
    )
    group = result.scalar_one()

    user = UserModel(
        email="stripe_test@example.com",
        hashed_password="mock_password",
        group_id=group.id,
        is_active=True
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function", autouse=True)
async def override_auth(test_user: UserModel):
    app.dependency_overrides[get_current_user] = lambda: test_user

    async def mock_get_current_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="insufficient access rights"
        )

    app.dependency_overrides[get_current_admin] = mock_get_current_admin

    yield

    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_current_admin, None)


@pytest_asyncio.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac