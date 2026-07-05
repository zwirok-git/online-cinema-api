from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from exceptions.auth import TokenExceptions, UserExceptions
from models.users import UserModel
from repositories.orders import OrderRepository
from repositories.payments import PaymentRepository
from repositories.tokens import TokenRepository
from repositories.users import GroupRepository, UserRepository
from security.jwt_tokens import JWTService
from services.payments import StripePaymentService
from services.payments.base_payment import IPaymentService
from services.tokens import TokenService
from services.users import UserService


http_bearer = HTTPBearer()


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


async def get_token_service(
    db_session: Annotated[AsyncSession, Depends(get_db)],
):
    return TokenService(TokenRepository(session=db_session))


async def get_jwt_service():
    return JWTService()


async def get_current_user(
    token: Annotated[str, Depends(http_bearer)],
    user_service: Annotated[UserService, Depends(get_user_service)],
    jwt_service: Annotated[JWTService, Depends(get_jwt_service)],
) -> UserModel:
    access_token = token.credentials
    try:
        payload = jwt_service.decode_token(access_token)
        user_id = int(payload.get("sub"))
        user = await user_service.get_user_by_id(user_id=user_id)
    except (TokenExceptions, UserExceptions) as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
            headers={"WWW-Authenticate": "Bearer"},
        ) from error

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive.",
        )
    return user
