from datetime import timezone, datetime, timedelta
from unittest.mock import patch, AsyncMock
import pytest
from sqlalchemy import select

from models import UserProfileModel
from repositories.tokens import TokenRepository
from security.passwords import verify_password
from api.dependencies import get_user_service
from models.users import UserGroupModel, UserGroupEnum, UserModel
from repositories.users import UserRepository
from services.tokens import TokenService
from exceptions.auth import (
    UserAlreadyExists,
    GroupDoesNotExist,
    UserDoesNotExists,
    UserAlreadyActivated,
    TokenDoesNotExists,
    TokenAlreadyExpired,
    UserNotActivated,
    InvalidToken,
    InvalidCredentials,
    InvalidOldPassword,
)


@pytest.fixture
async def user_service(db_session):
    from services.jwt_tokens import JWTService

    return await get_user_service(
        db_session=db_session,
        token_service=TokenService(TokenRepository(db_session)),
        jwt_service=JWTService(),
    )


@pytest.fixture(autouse=True)
def mock_send_email():
    with patch("services.users.send_email_task") as mock:
        yield mock


async def create_active_user(
    db_session, user_service, email="user@example.com", password="Pass123"
):
    user = await user_service.register_user(email=email, raw_password=password)
    token_service = TokenService(TokenRepository(db_session))
    token = await token_service.get_activation_token_by_user_id(user.id)
    await user_service.activate_user(token=token.token)
    return user


@pytest.mark.asyncio
async def test_service_get_user_by_id_successful(
    db_session, user_service, mock_send_email
):
    user = await user_service.register_user(
        email="dup@example.com", raw_password="Pass123"
    )
    retrieved_user = await user_service.get_user_by_id(user.id)
    assert retrieved_user is not None
    assert retrieved_user.id == user.id
    assert retrieved_user.email == user.email


@pytest.mark.asyncio
async def test_service_get_user_by_id_with_exceptions(
    db_session, user_service, mock_send_email
):
    with pytest.raises(UserDoesNotExists):
        user = await user_service.get_user_by_id(1000)


@pytest.mark.asyncio
async def test_register_user_persists_user_profile_and_commits(
    db_session, user_service, mock_send_email
):
    user = await user_service.register_user(
        email="test@example.com", raw_password="StrongPass123"
    )

    assert user.id is not None
    assert user.email == "test@example.com"
    assert verify_password("StrongPass123", user.hashed_password)
    assert user.is_active is False

    exists = await user_service.exists_by_email(email="test@example.com")
    assert exists is True
    mock_send_email.delay.assert_called_once()


@pytest.mark.asyncio
async def test_register_user_creates_associated_profile(
    db_session, user_service, mock_send_email
):
    user = await user_service.register_user(
        email="profile@example.com", raw_password="StrongPass123"
    )

    stmt = select(UserProfileModel).where(UserProfileModel.user_id == user.id)
    result = await db_session.execute(stmt)
    profile = result.scalar_one_or_none()
    assert profile is not None
    assert profile.user_id == user.id


@pytest.mark.asyncio
async def test_register_user_creates_activation_token(
    db_session, user_service, mock_send_email
):
    user = await user_service.register_user(
        email="activate@example.com", raw_password="StrongPass123"
    )
    token = await TokenService(
        TokenRepository(db_session)
    ).get_activation_token_by_user_id(user.id)
    assert token is not None


@pytest.mark.asyncio
async def test_register_user_raises_if_email_already_taken(
    db_session, user_service, mock_send_email
):

    await user_service.register_user(
        email="dup@example.com", raw_password="Pass123"
    )
    with pytest.raises(UserAlreadyExists):
        await user_service.register_user(
            email="dup@example.com", raw_password="Pass456"
        )
    assert mock_send_email.delay.call_count == 1


@pytest.mark.asyncio
async def test_register_user_raises_if_default_group_missing(
    db_session, user_service, mock_send_email
):
    user_service.group_repository.get_group_by_name = AsyncMock(
        return_value=None
    )
    with pytest.raises(GroupDoesNotExist):
        await user_service.register_user(
            email="test@example.com", raw_password="password"
        )


@pytest.mark.asyncio
async def test_resend_activation_token_successful(
    db_session, user_service, mock_send_email
):
    user = await user_service.register_user(
        email="default@example.com", raw_password="Pass123"
    )
    token_repository = TokenRepository(db_session)
    token_service = TokenService(token_repository)

    old_token = await token_service.get_activation_token_by_user_id(user.id)
    assert old_token is not None
    mock_send_email.reset_mock()

    await user_service.resend_activation_token(email=user.email)

    new_token = await token_service.get_activation_token_by_user_id(user.id)
    assert new_token is not None
    assert new_token.token != old_token.token

    old_token_exists = await token_repository.get_activation_token_by_token(
        old_token.token
    )
    assert old_token_exists is None
    mock_send_email.delay.assert_called_once()


@pytest.mark.asyncio
async def test_resend_activation_token_raises_if_user_not_found(
    db_session, user_service
):
    with pytest.raises(UserDoesNotExists):
        await user_service.resend_activation_token("missing@example.com")


@pytest.mark.asyncio
@patch("services.users.send_email_task")
async def test_resend_activation_token_raises_if_user_already_activated(
    mock_send_email, db_session, user_service
):
    user = await user_service.register_user(
        email="default@example.com", raw_password="Pass123"
    )
    user.is_active = True
    db_session.add(user)
    await db_session.commit()

    with pytest.raises(UserAlreadyActivated):
        await user_service.resend_activation_token(email=user.email)


@pytest.mark.asyncio
async def test_activate_user_successful(
    db_session, user_service, mock_send_email
):
    user = await user_service.register_user(
        email="default@example.com", raw_password="Pass123"
    )
    token_repository = TokenRepository(db_session)
    token_service = TokenService(token_repository)
    token = await token_service.get_activation_token_by_user_id(user.id)
    assert token is not None
    assert user.is_active is False

    activated_user = await user_service.activate_user(token=token.token)
    assert activated_user is not None
    assert activated_user.id == user.id
    assert activated_user.is_active is True

    token_exists = await token_repository.get_activation_token_by_user_id(
        activated_user.id
    )
    assert token_exists is None


@pytest.mark.asyncio
async def test_activate_user_raises_if_token_does_not_exists(
    db_session, user_service
):
    with pytest.raises(TokenDoesNotExists):
        await user_service.activate_user("does-not-exists")


@pytest.mark.asyncio
async def test_activate_user_raises_if_token_already_expired(
    db_session, user_service, mock_send_email
):
    user = await user_service.register_user(
        email="expired@example.com", raw_password="Pass123"
    )
    token_service = TokenService(TokenRepository(db_session))
    token = await token_service.get_activation_token_by_user_id(user.id)
    assert token is not None
    assert user.is_active is False

    token.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db_session.add(token)
    await db_session.commit()

    with pytest.raises(TokenAlreadyExpired):
        await user_service.activate_user(token.token)


@pytest.mark.asyncio
async def test_activate_user_raises_if_user_missing(
    db_session, user_service, mock_send_email
):
    user = await user_service.register_user(
        email="ghost@example.com", raw_password="Pass123"
    )
    token_service = TokenService(TokenRepository(db_session))
    token = await token_service.get_activation_token_by_user_id(user.id)
    await db_session.delete(user)
    await db_session.commit()

    with pytest.raises(TokenDoesNotExists):
        await user_service.activate_user(token.token)


@pytest.mark.asyncio
async def test_login_user_successful(db_session, user_service):
    user = await create_active_user(
        db_session, user_service, email="login@example.com", password="Pass123"
    )
    refresh_token, access_token = await user_service.login_user(
        email="login@example.com", password="Pass123"
    )

    assert refresh_token is not None
    assert access_token is not None
    assert refresh_token != access_token

    token_service = TokenService(TokenRepository(db_session))
    token = await token_service.get_refresh_token_by_token(refresh_token)
    assert token is not None
    assert user.id == token.user_id


@pytest.mark.asyncio
async def test_login_user_raises_if_user_not_found(db_session, user_service):
    with pytest.raises(InvalidCredentials):
        await user_service.login_user(
            email="missing@example.com", password="Pass123"
        )


@pytest.mark.asyncio
async def test_login_user_raises_if_password_incorrect(
    db_session, user_service
):
    user = await create_active_user(
        db_session, user_service, email="wrong@example.com", password="Pass123"
    )
    with pytest.raises(InvalidCredentials):
        await user_service.login_user(
            email="wrong@example.com", password="Wrong1Password"
        )


@pytest.mark.asyncio
async def test_login_user_raises_if_user_not_activated(
    db_session, user_service
):
    user = await user_service.register_user(
        email="inactive@gmail.com", raw_password="Pass123"
    )
    with pytest.raises(UserNotActivated):
        await user_service.login_user(
            email="inactive@gmail.com", password="Pass123"
        )


@pytest.mark.asyncio
async def test_logout_user_successful_and_delete_refresh_tokens(
    db_session, user_service
):
    user = await create_active_user(
        db_session, user_service, email="logout@gmail.com", password="Pass123"
    )
    refresh_token, _ = await user_service.login_user(
        email="logout@gmail.com", password="Pass123"
    )
    token_service = TokenService(TokenRepository(db_session))
    assert (
        await token_service.get_refresh_token_by_token(refresh_token)
        is not None
    )
    await user_service.logout_user(user.id)
    with pytest.raises(TokenDoesNotExists):
        await token_service.get_activation_token_by_token(refresh_token)


@pytest.mark.asyncio
async def test_refresh_access_token_successful(db_session, user_service):
    await create_active_user(
        db_session, user_service, email="refresh@example.com"
    )
    old_refresh_token, _ = await user_service.login_user(
        email="refresh@example.com", password="Pass123"
    )

    new_refresh_token, new_access_token = (
        await user_service.refresh_access_token(
            refresh_token=old_refresh_token
        )
    )

    assert new_refresh_token
    assert new_access_token


@pytest.mark.asyncio
async def test_refresh_access_token_raises_if_token_not_a_refresh_token(
    db_session, user_service
):
    user = await create_active_user(
        db_session, user_service, email="notrefresh@example.com"
    )

    access_token = user_service.jwt_service.create_access_token(
        data={"user_id": user.id}
    )

    with pytest.raises(InvalidToken):
        await user_service.refresh_access_token(refresh_token=access_token)


@pytest.mark.asyncio
async def test_refresh_access_token_raises_if_token_not_persisted(
    db_session, user_service
):
    user = await create_active_user(
        db_session, user_service, email="ghosttoken@example.com"
    )

    unstored_refresh_token = user_service.jwt_service.create_refresh_token(
        data={"user_id": user.id}
    )

    with pytest.raises(TokenDoesNotExists):
        await user_service.refresh_access_token(
            refresh_token=unstored_refresh_token
        )


@pytest.mark.asyncio
async def test_change_password_successful(db_session, user_service):
    user = await create_active_user(
        db_session,
        user_service,
        email="changepass@example.com",
        password="Pass123",
    )
    refresh_token, _ = await user_service.login_user(
        email="changepass@example.com", password="Pass123"
    )

    await user_service.change_password(
        user=user, new_password="NewPass456", old_password="Pass123"
    )

    persisted = await user_service.get_user_by_id(user.id)
    assert verify_password("NewPass456", persisted.hashed_password)


@pytest.mark.asyncio
async def test_change_password_raises_if_old_password_incorrect(
    db_session, user_service
):
    user = await create_active_user(
        db_session,
        user_service,
        email="badoldpass@example.com",
        password="Pass123",
    )

    with pytest.raises(InvalidOldPassword):
        await user_service.change_password(
            user=user, new_password="NewPass456", old_password="WrongOldPass"
        )
    persisted = await user_service.get_user_by_id(user.id)
    assert verify_password("Pass123", persisted.hashed_password)


@pytest.mark.asyncio
async def test_reset_password_successful(
    db_session, user_service, mock_send_email
):
    user = await create_active_user(
        db_session, user_service, email="reset@example.com"
    )
    mock_send_email.reset_mock()

    await user_service.reset_password(user_email="reset@example.com")

    token_service = TokenService(TokenRepository(db_session))
    reset_token = await token_service.get_reset_token_by_user_id(
        user_id=user.id
    )
    assert reset_token is not None
    mock_send_email.delay.assert_called_once()


@pytest.mark.asyncio
async def test_reset_password_replaces_existing_token(
    db_session, user_service, mock_send_email
):
    user = await create_active_user(
        db_session, user_service, email="resettwice@example.com"
    )

    await user_service.reset_password(user_email="resettwice@example.com")
    token_service = TokenService(TokenRepository(db_session))
    first_token = await token_service.get_reset_token_by_user_id(
        user_id=user.id
    )

    await user_service.reset_password(user_email="resettwice@example.com")
    second_token = await token_service.get_reset_token_by_user_id(
        user_id=user.id
    )

    assert second_token.token != first_token.token
    with pytest.raises(TokenDoesNotExists):
        await token_service.get_reset_token_by_token(
            token_value=first_token.token
        )


@pytest.mark.asyncio
async def test_reset_password_raises_if_user_not_found(
    db_session, user_service
):
    with pytest.raises(UserDoesNotExists):
        await user_service.reset_password(user_email="missing@example.com")


@pytest.mark.asyncio
async def test_reset_password_complete_successful(db_session, user_service):
    user = await create_active_user(
        db_session, user_service, email="completereset@example.com"
    )
    await user_service.reset_password(user_email="completereset@example.com")

    token_service = TokenService(TokenRepository(db_session))
    reset_token = await token_service.get_reset_token_by_user_id(
        user_id=user.id
    )

    await user_service.reset_password_complete(
        reset_token=reset_token.token, new_password="BrandNewPass789"
    )

    stmt = select(UserModel).where(UserModel.id == user.id)
    result = await db_session.execute(stmt)
    persisted = result.scalar_one()
    assert verify_password("BrandNewPass789", persisted.hashed_password)
    with pytest.raises(TokenDoesNotExists):
        await token_service.get_reset_token_by_token(
            token_value=reset_token.token
        )


@pytest.mark.asyncio
async def test_reset_password_complete_raises_if_token_invalid(
    db_session, user_service
):
    with pytest.raises(TokenDoesNotExists):
        await user_service.reset_password_complete(
            reset_token="does-not-exist", new_password="Whatever123"
        )


@pytest.mark.asyncio
async def test_reset_password_complete_raises_if_user_missing(
    db_session, user_service
):
    user = await create_active_user(
        db_session, user_service, email="resetghost@example.com"
    )
    await user_service.reset_password(user_email="resetghost@example.com")

    token_service = TokenService(TokenRepository(db_session))
    reset_token = await token_service.get_reset_token_by_user_id(
        user_id=user.id
    )

    await db_session.delete(user)
    await db_session.commit()

    with pytest.raises(TokenDoesNotExists):
        await user_service.reset_password_complete(
            reset_token=reset_token.token, new_password="Whatever123"
        )


@pytest.mark.asyncio
async def test_get_me_profile_successful(db_session, user_service):
    user = await create_active_user(
        db_session, user_service, email="me@example.com"
    )

    result = await user_service.get_me_profile(user=user)
    assert result.id == user.id


@pytest.mark.asyncio
async def test_get_me_profile_raises_if_user_missing(db_session, user_service):
    user = await create_active_user(
        db_session, user_service, email="deletedme@example.com"
    )
    await db_session.delete(user)
    await db_session.commit()

    with pytest.raises(UserDoesNotExists):
        await user_service.get_me_profile(user=user)


@pytest.mark.asyncio
async def test_change_profile_successful(db_session, user_service):
    user = await create_active_user(
        db_session, user_service, email="profileupdate@example.com"
    )

    updated = await user_service.change_profile(
        user=user, profile_data={"first_name": "Jane"}
    )

    stmt = select(UserProfileModel).where(UserProfileModel.user_id == user.id)
    result = await db_session.execute(stmt)
    persisted_profile = result.scalar_one()
    assert persisted_profile.first_name == "Jane"
    assert updated.id == user.id


@pytest.mark.asyncio
async def test_change_profile_raises_if_user_missing(db_session, user_service):
    user = await create_active_user(
        db_session, user_service, email="ghostprofile@example.com"
    )
    await db_session.delete(user)
    await db_session.commit()

    with pytest.raises(UserDoesNotExists):
        await user_service.change_profile(
            user=user, profile_data={"first_name": "Ghost"}
        )


@pytest.mark.asyncio
async def test_get_all_users_returns_users_and_total_count(
    db_session, user_service
):
    for i in range(2):
        await create_active_user(
            db_session, user_service, email=f"user{i}@example.com"
        )

    users, total = await user_service.get_all_users(limit=2, offset=0)

    assert total == 3
    assert len(users) == 2


@pytest.mark.asyncio
async def test_get_all_users_respects_offset(db_session, user_service):
    for i in range(2):
        await create_active_user(
            db_session, user_service, email=f"offset{i}@example.com"
        )

    users, total = await user_service.get_all_users(limit=10, offset=2)

    assert total == 3
    assert len(users) == 1


@pytest.mark.asyncio
async def test_change_group_successful(db_session, user_service):
    user = await create_active_user(
        db_session, user_service, email="changegroup@example.com"
    )

    updated = await user_service.change_group(
        user_id=user.id, group_name=UserGroupEnum.MODERATOR.name
    )

    assert updated.group.name == UserGroupEnum.MODERATOR

    persisted = await user_service.get_user_by_id(user_id=user.id)
    assert persisted.group.name == UserGroupEnum.MODERATOR


@pytest.mark.asyncio
async def test_change_group_raises_if_user_missing(db_session, user_service):
    with pytest.raises(UserDoesNotExists):
        await user_service.change_group(
            user_id=999999, group_name=UserGroupEnum.MODERATOR.name
        )


@pytest.mark.asyncio
async def test_change_status_activates_user(db_session, user_service):
    user = await user_service.register_user(
        email="statuschange@example.com", raw_password="Pass123"
    )
    assert user.is_active is False

    updated = await user_service.change_status(user_id=user.id)
    assert updated.is_active is True

    persisted = await user_service.get_user_by_id(user_id=user.id)
    assert persisted.is_active is True


@pytest.mark.asyncio
async def test_change_status_raises_if_user_missing(db_session, user_service):
    with pytest.raises(UserDoesNotExists):
        await user_service.change_status(user_id=999999)
