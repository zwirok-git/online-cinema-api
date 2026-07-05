from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from core.database import get_db
from exceptions.auth import PermissionDenied, TokenExceptions, UserExceptions
from models.users import UserGroupEnum, UserModel
from repositories.users import GroupRepository, UserRepository
from security.jwt_tokens import JWTService
from services.users import UserService


bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials, Depends(bearer_scheme)
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserModel:
    jwt_service = JWTService()
    user_service = UserService(UserRepository(db), GroupRepository(db))

    try:
        payload = jwt_service.decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise PermissionDenied("Invalid token type.")

        user_id = payload.get("sub")
        if user_id is None:
            raise PermissionDenied("Invalid token payload.")

        user = await user_service.get_user_by_id(int(user_id))
        if not user.is_active:
            raise PermissionDenied("User is inactive.")
        return user
    except (TokenExceptions, UserExceptions, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
        ) from error


def require_roles(*roles: UserGroupEnum):
    async def dependency(
        current_user: Annotated[UserModel, Depends(get_current_user)]
    ) -> UserModel:
        try:
            UserService.ensure_user_has_role(current_user, roles)
        except PermissionDenied as error:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(error),
            ) from error
        return current_user

    return dependency
