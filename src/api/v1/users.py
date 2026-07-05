from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from api.dependencies.auth import get_current_user, require_roles
from core.database import get_db
from exceptions.auth import TokenExceptions, UserExceptions
from models.users import UserGroupEnum, UserModel
from repositories.tokens import TokenRepository
from repositories.users import GroupRepository, UserRepository
from schemas.tokens import (
    AccessTokenResponseSchema,
    LogoutRequestSchema,
    RefreshTokenRequestSchema,
    TokenPairResponseSchema,
)
from schemas.users import (
    EmailRequestSchema,
    MessageResponseSchema,
    PasswordChangeRequestSchema,
    PasswordResetRequestSchema,
    UserGroupUpdateRequestSchema,
    UserLoginRequestSchema,
    UserRegisterRequestSchema,
    UserRegisterResponseSchema,
)
from security.jwt_tokens import JWTService
from services.email import send_activation_email, send_password_reset_email
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
        user_model = await user_service.create_user(
            email=user.email, raw_password=user.password
        )
        await token_service.create_activation_token(user_id=user_model.id)
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
            id=user_model.id,
            email=user_model.email,
            created_at=user_model.created_at,
            is_active=user_model.is_active,
        )


@router.get("/activate", response_model=UserRegisterResponseSchema)
async def activate(
    db: Annotated[AsyncSession, Depends(get_db)],
    activation_token: str,
):
    token_service = TokenService(TokenRepository(db))
    try:
        user = await token_service.activate_user(
            token_value=activation_token
        )
        await db.commit()
        return user
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


@router.post("/resend-activation", response_model=MessageResponseSchema)
async def resend_activation(
    db: Annotated[AsyncSession, Depends(get_db)],
    request: EmailRequestSchema,
):
    user_service = UserService(UserRepository(db), GroupRepository(db))
    token_service = TokenService(TokenRepository(db))
    try:
        user = await user_service.get_user_by_email(email=request.email)
        token = await token_service.resend_activation_token(user)
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

    await send_activation_email(user.email, token.token)
    return MessageResponseSchema(message="Activation email was sent.")


@router.post("/login", response_model=TokenPairResponseSchema)
async def login(
    db: Annotated[AsyncSession, Depends(get_db)], user: UserLoginRequestSchema
):
    user_service = UserService(UserRepository(db), GroupRepository(db))
    token_service = TokenService(TokenRepository(db))
    jwt_service = JWTService()
    try:
        user_model = await user_service.get_user_by_email(email=user.email)
        await user_service.validate_credentials(user.email, user.password)
        refresh_token = await token_service.create_refresh_token(
            user_id=user_model.id
        )
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

    jwt_access_token = jwt_service.create_access_token(
        {"user_id": user_model.id}
    )
    return TokenPairResponseSchema(
        access_token=jwt_access_token,
        refresh=refresh_token.token,
    )


@router.post("/refresh", response_model=AccessTokenResponseSchema)
async def refresh(
    db: Annotated[AsyncSession, Depends(get_db)],
    request: RefreshTokenRequestSchema,
):
    token_service = TokenService(TokenRepository(db))
    try:
        access_token = await token_service.refresh_access_token(
            request.refresh_token
        )
        await db.commit()
    except TokenExceptions as error:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
        ) from error
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the request.",
        ) from None

    return AccessTokenResponseSchema(access_token=access_token)


@router.post("/logout", response_model=MessageResponseSchema)
async def logout(
    db: Annotated[AsyncSession, Depends(get_db)],
    request: LogoutRequestSchema,
):
    token_service = TokenService(TokenRepository(db))
    try:
        await token_service.revoke_refresh_token(request.refresh_token)
        await db.commit()
    except TokenExceptions as error:
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

    return MessageResponseSchema(message="Logged out successfully.")


@router.post("/password/forgot", response_model=MessageResponseSchema)
async def forgot_password(
    db: Annotated[AsyncSession, Depends(get_db)],
    request: EmailRequestSchema,
):
    user_service = UserService(UserRepository(db), GroupRepository(db))
    token_service = TokenService(TokenRepository(db))

    try:
        user = await user_service.get_user_by_email(email=request.email)
        token = await token_service.create_password_reset_token(user)
        await db.commit()
    except UserExceptions:
        await db.rollback()
        return MessageResponseSchema(
            message="If this email exists, password reset email was sent."
        )
    except TokenExceptions as error:
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

    await send_password_reset_email(user.email, token.token)
    return MessageResponseSchema(
        message="If this email exists, password reset email was sent."
    )


@router.post("/password/reset", response_model=MessageResponseSchema)
async def reset_password(
    db: Annotated[AsyncSession, Depends(get_db)],
    request: PasswordResetRequestSchema,
):
    token_service = TokenService(TokenRepository(db))
    try:
        await token_service.reset_password(
            token_value=request.token,
            new_password=request.password,
        )
        await db.commit()
    except TokenExceptions as error:
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

    return MessageResponseSchema(message="Password was reset successfully.")


@router.post("/password/change", response_model=MessageResponseSchema)
async def change_password(
    db: Annotated[AsyncSession, Depends(get_db)],
    request: PasswordChangeRequestSchema,
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    user_service = UserService(UserRepository(db), GroupRepository(db))
    token_service = TokenService(TokenRepository(db))
    try:
        await user_service.change_password(
            user=current_user,
            old_password=request.old_password,
            new_password=request.password,
        )
        await token_service.token_repository.delete_user_refresh_tokens(
            user_id=current_user.id
        )
        await db.commit()
    except UserExceptions as error:
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

    return MessageResponseSchema(message="Password was changed successfully.")


@router.patch(
    "/{user_id}/activate",
    response_model=UserRegisterResponseSchema,
)
async def manually_activate_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: int,
    _: Annotated[
        UserModel, Depends(require_roles(UserGroupEnum.ADMIN))
    ],
):
    user_service = UserService(UserRepository(db), GroupRepository(db))
    try:
        user = await user_service.manually_activate_user(user_id=user_id)
        await db.commit()
        return user
    except UserExceptions as error:
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


@router.patch("/{user_id}/group", response_model=UserRegisterResponseSchema)
async def update_user_group(
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: int,
    request: UserGroupUpdateRequestSchema,
    _: Annotated[
        UserModel, Depends(require_roles(UserGroupEnum.ADMIN))
    ],
):
    user_service = UserService(UserRepository(db), GroupRepository(db))
    try:
        user = await user_service.set_user_group(
            user_id=user_id,
            group=request.group,
        )
        await db.commit()
        return user
    except UserExceptions as error:
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
