from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from exceptions.auth import UserDoesNotExists
from models.users import UserModel
from repositories.orders import OrderRepository
from repositories.payments import PaymentRepository
from repositories.users import GroupRepository, UserRepository
from services.payments import StripePaymentService
from services.payments.base_payment import IPaymentService
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


async def get_user_service(
    db_session: Annotated[AsyncSession, Depends(get_db)],
) -> UserService:
    return UserService(
        user_repository=UserRepository(db_session),
        group_repository=GroupRepository(db_session),
    )


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserModel:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.TOKEN_SECRET_KEY,
            algorithms=[settings.TOKEN_ALGORITHM],
        )
        email: str | None = payload.get("sub")
        if email is None:
            raise credentials_exception
    except (jwt.PyJWTError, ValueError):
        raise credentials_exception from None

    try:
        user = await user_service.get_user_by_email(email=email)
    except UserDoesNotExists:
        raise credentials_exception from None

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )

    return user
