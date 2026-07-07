from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.params import Query
from starlette import status

from api.dependencies import (
    get_current_only_admin,
    get_current_user,
    get_user_service,
)
from models import UserModel
from schemas.tokens import TokenPairResponseSchema, TokenRefreshRequestSchema
from schemas.users import (
    UserGroupRequestSchema,
    UserGroupResponseSchema,
    UserListItemResponseSchema,
    UserListResponseSchema,
    UserLoginRequestSchema,
    UserMeRequestSchema,
    UserMeResponseSchema,
    UserMessageSchema,
    UserNewPasswordRequestSchema,
    UserPasswordChangeRequestSchema,
    UserRegisterRequestSchema,
    UserRegisterResponseSchema,
    UserResendActivationSchema,
    UserResetRequestSchema,
)
from services.users import UserService

from src.schemas.users import UserAvatarResponseSchema

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "/register",
    response_model=UserRegisterResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="User Registration",
    description="Register a new user with an email and password.",
    responses={
        404: {
            "description": "Default user group with does not exists.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Default user group with does not exists."
                    }
                }
            },
        },
        409: {
            "description": "User with this email already exists.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "A user with this email already exists."
                    }
                }
            },
        },
    },
)
async def register(
    user_service: Annotated[UserService, Depends(get_user_service)],
    user: UserRegisterRequestSchema,
):
    user_model = await user_service.register_user(
        email=user.email,
        raw_password=user.password,
    )
    return UserRegisterResponseSchema(
        id=user_model.id,
        email=user_model.email,
        created_at=user_model.created_at,
        is_active=user_model.is_active,
    )


@router.post(
    "/resend_activation",
    response_model=UserMessageSchema,
    summary="Resend account activation email.",
    description="Generates a new activation token and resends the "
    "activation link to the user's email address.",
    responses={
        400: {
            "description": "User already activated.",
            "content": {
                "application/json": {
                    "example": {"detail": "User already activated."}
                }
            },
        },
        404: {
            "description": "User with this email does not exist.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User with this email does not exist."
                    }
                }
            },
        },
    },
)
async def resend_activation(
    user_service: Annotated[UserService, Depends(get_user_service)],
    user: UserResendActivationSchema,
):
    await user_service.resend_activation_token(email=user.email)
    return UserMessageSchema(
        message="Your activation link has been sent to your email address.",
    )


@router.get(
    "/activate",
    response_model=UserRegisterResponseSchema,
    summary="Activate user account via token.",
    description="Activates a user's account using the activation token.",
    responses={
        403: {
            "description": "Activation token has already expired.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Activation token has already expired."
                    }
                }
            },
        },
        404: {
            "description": "Activation token does not exist.",
            "content": {
                "application/json": {
                    "example": {"detail": "Activation token does not exist."}
                }
            },
        },
    },
)
async def activate(
    user_service: Annotated[UserService, Depends(get_user_service)],
    activation_token: str,
):
    user_model = await user_service.activate_user(token=activation_token)
    return UserRegisterResponseSchema(
        id=user_model.id,
        email=user_model.email,
        created_at=user_model.created_at,
        is_active=user_model.is_active,
    )


@router.post(
    "/login",
    response_model=TokenPairResponseSchema,
    summary="Log in user and obtain access/refresh tokens.",
    description=(
        "Authenticates a user by email and password, and returns "
        "a pair of tokens."
    ),
    responses={
        401: {
            "description": "Invalid email or password.",
            "content": {
                "application/json": {"detail": "Invalid email or password."}
            },
        },
        403: {
            "description": "Account exists but is not activated yet.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Account exists but is not activated yet."
                    }
                }
            },
        },
    },
)
async def login(
    user_service: Annotated[UserService, Depends(get_user_service)],
    user_data: UserLoginRequestSchema,
):
    refresh_token, access_token = await user_service.login_user(
        email=user_data.email,
        password=user_data.password,
    )
    return TokenPairResponseSchema(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenPairResponseSchema)
async def refresh(
    user_service: Annotated[UserService, Depends(get_user_service)],
    token: TokenRefreshRequestSchema,
):
    access_token, refresh_token = await user_service.refresh_access_token(
        refresh_token=token.refresh_token
    )
    return TokenPairResponseSchema(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Log out and revoke all refresh tokens",
    description=(
        "Logs out the currently authenticated user by deleting all of "
        "their refresh tokens."
    ),
    responses={
        401: {
            "description": "Missing, invalid, or expired access token.",
            "content": {
                "application/json": {
                    "example": {"detail": "Could not validate credentials"}
                }
            },
        },
        403: {
            "description": "Account exists but is not activated yet.",
            "content": {
                "application/json": {
                    "detail": "Account exists but is not activated yet."
                }
            },
        },
    },
)
async def logout(
    user_service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    await user_service.logout_user(user_id=current_user.id)


@router.post(
    "/password/change",
    response_model=UserMessageSchema,
)
async def change_password(
    user_service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
    change_data: UserPasswordChangeRequestSchema,
):
    await user_service.change_password(
        user=current_user,
        old_password=change_data.old_password,
        new_password=change_data.new_password,
    )
    return UserMessageSchema(
        message="Password has been changed.",
    )


@router.post("/password/reset", response_model=UserMessageSchema)
async def reset_password(
    user_service: Annotated[UserService, Depends(get_user_service)],
    reset_password_data: UserResetRequestSchema,
):
    await user_service.reset_password(
        user_email=reset_password_data.email,
    )
    return UserMessageSchema(
        message="Your reset link has been sent to your email address.",
    )


@router.post("/password/reset/complete", response_model=UserMessageSchema)
async def password_reset_complete(
    user_service: Annotated[UserService, Depends(get_user_service)],
    reset_token: Annotated[str, Query()],
    user_data: UserNewPasswordRequestSchema,
):
    await user_service.reset_password_complete(
        reset_token=reset_token,
        new_password=user_data.new_password,
    )
    return UserMessageSchema(
        message="Password has been reset.",
    )


@router.get("/me", response_model=UserMeResponseSchema)
async def me(
    user_service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    user_model = await user_service.get_me_profile(user=current_user)
    return UserMeResponseSchema(
        id=user_model.id,
        email=user_model.email,
        created_at=user_model.created_at,
        group=UserGroupResponseSchema.model_validate(user_model.group),
        is_active=user_model.is_active,
        first_name=user_model.profile.first_name,
        last_name=user_model.profile.last_name,
        avatar=user_model.profile.avatar,
        date_of_birth=user_model.profile.date_of_birth,
        gender=user_model.profile.gender,
        info=user_model.profile.info,
    )


@router.patch("/me", response_model=UserMeResponseSchema)
async def me_patch(
    user_service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
    profile_data: UserMeRequestSchema,
):
    update_fields = profile_data.model_dump(exclude_unset=True)
    user_model = await user_service.change_profile(
        user=current_user, profile_data=update_fields
    )
    return UserMeResponseSchema(
        id=user_model.id,
        email=user_model.email,
        created_at=user_model.created_at,
        group=UserGroupResponseSchema.model_validate(user_model.group),
        is_active=user_model.is_active,
        first_name=user_model.profile.first_name,
        last_name=user_model.profile.last_name,
        avatar=user_model.profile.avatar,
        date_of_birth=user_model.profile.date_of_birth,
        gender=user_model.profile.gender,
        info=user_model.profile.info,
    )


@router.get("", response_model=UserListResponseSchema)
async def list_users(
    user_service: Annotated[UserService, Depends(get_user_service)],
    current_admin: Annotated[UserModel, Depends(get_current_only_admin)],
    limit: Annotated[int, Query(gt=0, le=20)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    users_models, total_users = await user_service.get_all_users(
        limit=limit,
        offset=offset,
    )
    return UserListResponseSchema(
        users=[
            UserListItemResponseSchema.model_validate(user_model)
            for user_model in users_models
        ],
        total_users=total_users,
    )


@router.get("/{user_id}", response_model=UserMeResponseSchema)
async def get_user_by_id(
    user_service: Annotated[UserService, Depends(get_user_service)],
    current_admin: Annotated[UserModel, Depends(get_current_only_admin)],
    user_id: int,
):
    user_model = await user_service.get_user_by_id(
        user_id=user_id, with_relations=True
    )
    return UserMeResponseSchema(
        id=user_model.id,
        email=user_model.email,
        created_at=user_model.created_at,
        group=UserGroupResponseSchema.model_validate(user_model.group),
        is_active=user_model.is_active,
        first_name=user_model.profile.first_name,
        last_name=user_model.profile.last_name,
        avatar=user_model.profile.avatar,
        date_of_birth=user_model.profile.date_of_birth,
        gender=user_model.profile.gender,
        info=user_model.profile.info,
    )


@router.get("/{user_id}/change/group", response_model=UserMeResponseSchema)
async def change_group(
    user_service: Annotated[UserService, Depends(get_user_service)],
    current_admin: Annotated[UserModel, Depends(get_current_only_admin)],
    group_data: UserGroupRequestSchema,
    user_id: int,
):
    user_model = await user_service.change_group(
        user_id=user_id, group_name=str(group_data.name.name)
    )
    return UserMeResponseSchema(
        id=user_model.id,
        email=user_model.email,
        created_at=user_model.created_at,
        group=UserGroupResponseSchema.model_validate(user_model.group),
        is_active=user_model.is_active,
        first_name=user_model.profile.first_name,
        last_name=user_model.profile.last_name,
        avatar=user_model.profile.avatar,
        date_of_birth=user_model.profile.date_of_birth,
        gender=user_model.profile.gender,
        info=user_model.profile.info,
    )


@router.get("/{user_id}/change/status", response_model=UserMeResponseSchema)
async def change_status(
    user_service: Annotated[UserService, Depends(get_user_service)],
    current_admin: Annotated[UserModel, Depends(get_current_only_admin)],
    user_id: int,
):
    user_model = await user_service.change_status(user_id=user_id)
    return UserMeResponseSchema(
        id=user_model.id,
        email=user_model.email,
        created_at=user_model.created_at,
        group=UserGroupResponseSchema.model_validate(user_model.group),
        is_active=user_model.is_active,
        first_name=user_model.profile.first_name,
        last_name=user_model.profile.last_name,
        avatar=user_model.profile.avatar,
        date_of_birth=user_model.profile.date_of_birth,
        gender=user_model.profile.gender,
        info=user_model.profile.info,
    )


@router.post("/me/avatar", response_model=UserAvatarResponseSchema)
async def upload_avatar(
    user_service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
    avatar: UploadFile = File(...),
):
    try:
        avatar_url = await user_service.upload_avatar(
            user=current_user,
            avatar=avatar,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from None

    return UserAvatarResponseSchema(avatar=avatar_url)
