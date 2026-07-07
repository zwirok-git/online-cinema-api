from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from exceptions.auth import (
    InvalidToken,
    TokenAlreadyExpired,
    UserDoesNotExists,
)
from models.users import UserGroupEnum, UserModel
from repositories.carts import CartRepository
from repositories.movies import MovieRepository
from repositories.orders import OrderRepository
from repositories.payments import PaymentRepository
from repositories.tokens import TokenRepository
from repositories.users import GroupRepository, UserRepository
from services.carts import CartService
from services.jwt_tokens import JWTService
from services.movies import MovieService
from services.orders import OrderService
from services.payments import StripePaymentService
from services.payments.base_payment import IPaymentService
from services.tokens import TokenService
from services.users import UserService


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")


async def get_payment_service(
    db_session: Annotated[AsyncSession, Depends(get_db)],
) -> IPaymentService:
    payment_repo = PaymentRepository(db_session)
    order_repo = OrderRepository(db_session)

    return StripePaymentService(
        payment_repo=payment_repo, order_repo=order_repo
    )


def get_jwt_service() -> JWTService:
    return JWTService()


async def get_token_service(
    db_session: Annotated[AsyncSession, Depends(get_db)],
) -> TokenService:
    return TokenService(token_repository=TokenRepository(db_session))


async def get_user_service(
    db_session: Annotated[AsyncSession, Depends(get_db)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
    jwt_service: Annotated[JWTService, Depends(get_jwt_service)],
) -> UserService:
    return UserService(
        session=db_session,
        user_repository=UserRepository(db_session),
        group_repository=GroupRepository(db_session),
        token_service=token_service,
        jwt_service=jwt_service,
    )


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_service: Annotated[UserService, Depends(get_user_service)],
    jwt_service: Annotated[JWTService, Depends(get_jwt_service)],
) -> UserModel:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt_service.decode_token(token)
    except (TokenAlreadyExpired, InvalidToken):
        raise credentials_exception from None

    if payload.get("type") != "access":
        raise credentials_exception

    raw_user_id = payload.get("sub")
    if raw_user_id is None:
        raise credentials_exception

    try:
        user = await user_service.get_user_by_id(user_id=int(raw_user_id))
    except UserDoesNotExists:
        raise credentials_exception from None

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )

    return user


async def get_current_admin(
    current_user: UserModel = Depends(get_current_user),
) -> UserModel:
    if not current_user.group or current_user.group.name not in (
        UserGroupEnum.ADMIN,
        UserGroupEnum.MODERATOR,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Only for moderators/admins.",
        )

    return current_user


async def get_current_only_admin(
    current_user: UserModel = Depends(get_current_user),
) -> UserModel:
    if (
        not current_user.group
        or current_user.group.name != UserGroupEnum.ADMIN
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Only for admins.",
        )

    return current_user


async def get_cart_service(
    db_session: Annotated[AsyncSession, Depends(get_db)],
) -> CartService:
    return CartService(
        cart_repo=CartRepository(db_session),
        order_repo=OrderRepository(db_session),
        user_repo=UserRepository(db_session),
    )


async def get_order_service(
    db_session: Annotated[AsyncSession, Depends(get_db)],
) -> OrderService:
    return OrderService(repo=OrderRepository(db_session))


async def get_movie_service(
    db_session: Annotated[AsyncSession, Depends(get_db)],
) -> MovieService:
    return MovieService(repo=MovieRepository(db_session))
