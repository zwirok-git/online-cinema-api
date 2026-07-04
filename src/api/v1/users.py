from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from core.config import settings
from core.database import get_db
from exceptions.auth import TokenExceptions, UserExceptions
from models.tokens import RefreshTokenModel
from repositories.tokens import TokenRepository
from repositories.users import GroupRepository, UserRepository
from schemas.tokens import TokenPairResponseSchema
from schemas.users import (
    UserLoginRequestSchema,
    UserRegisterRequestSchema,
    UserRegisterResponseSchema,
)
from security.jwt_tokens import JWTService
from services.tokens import TokenService
from services.users import UserService


router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", response_model=UserRegisterResponseSchema)
async def register(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: UserRegisterRequestSchema,
):
    user_service = UserService(UserRepository(db), GroupRepository(db))
    token_service = TokenService(TokenRepository(db))

    try:
        user = await user_service.create_user(
            email=user.email, raw_password=user.password
        )
        await token_service.create_activation_token(user_id=user.id)
        await db.commit()
    except (UserExceptions, TokenExceptions) as error:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error
    except Exception as error:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error
    else:
        # here send email
        return UserRegisterResponseSchema(
            id=user.id,
            email=user.email,
            created_at=user.created_at,
            is_active=user.is_active,
        )


@router.get("/activate", response_model=UserRegisterResponseSchema)
async def activate(
    db: Annotated[AsyncSession, Depends(get_db)],
    activation_token: str,
):
    token_service = TokenService(TokenRepository(db))
    user = await token_service.activate_user(token_value=activation_token)
    return user


@router.post("/login", response_model=TokenPairResponseSchema)
async def login(
    db: Annotated[AsyncSession, Depends(get_db)], user: UserLoginRequestSchema
):
    user_service = UserService(UserRepository(db), GroupRepository(db))
    jwt_service = JWTService()
    try:
        user = await user_service.get_user_by_email(email=user.email)
        await user_service.validate_credentials(
            user.email, user.hashed_password
        )
        jwt_refresh_token = jwt_service.create_refresh_token(
            data={"user_id": user.id}
        )
        refresh_token = RefreshTokenModel.create(
            user_id=user.id,
            expires_at=datetime.now(timezone.utc)
            + settings.REFRESH_TOKEN_EXPIRE,
            token=jwt_refresh_token,
        )
        db.add(refresh_token)
        await db.flush()
        await db.commit()
    except (UserExceptions, TokenExceptions) as error:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the request.",
        ) from None

    jwt_access_token = jwt_service.create_access_token({"user_id": user.id})
    return TokenPairResponseSchema(
        access_token=jwt_access_token,
        refresh=jwt_refresh_token,
    )
