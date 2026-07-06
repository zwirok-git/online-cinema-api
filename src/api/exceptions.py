from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from exceptions.payments import (
    InvalidOrderStatusException,
    OrderAccessDeniedException,
    OrderNotFoundException,
)


def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(OrderNotFoundException)
    async def order_not_found_handler(
        request: Request, exc: OrderNotFoundException
    ):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": exc.message},
        )

    @app.exception_handler(OrderAccessDeniedException)
    async def order_access_denied_handler(
        request: Request, exc: OrderAccessDeniedException
    ):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": exc.message},
        )

    @app.exception_handler(InvalidOrderStatusException)
    async def invalid_order_status_handler(
        request: Request, exc: InvalidOrderStatusException
    ):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": exc.message},
        )

    @app.exception_handler(UserAlreadyExists)
    async def user_already_exists_handler(
        request: Request, exc: UserAlreadyExists
    ):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": exc.message},
        )

    @app.exception_handler(GroupDoesNotExist)
    async def group_not_found_handler(
        request: Request, exc: GroupDoesNotExist
    ):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": exc.message},
        )

    @app.exception_handler(UserDoesNotExists)
    async def user_not_found_handler(request: Request, exc: UserDoesNotExists):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": exc.message},
        )

    @app.exception_handler(TokenDoesNotExists)
    async def token_not_found_handler(
        request: Request, exc: TokenDoesNotExists
    ):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": exc.message},
        )

    @app.exception_handler(TokenAlreadyExpired)
    async def token_expired_handler(
        request: Request, exc: TokenAlreadyExpired
    ):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": exc.message},
        )

    @app.exception_handler(InvalidCredentials)
    async def invalid_credentials_handler(
        request: Request, exc: InvalidCredentials
    ):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": exc.message},
        )

    @app.exception_handler(UserNotActivated)
    async def user_not_activated_handler(
        request: Request, exc: UserNotActivated
    ):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": exc.message},
        )

    @app.exception_handler(InvalidToken)
    async def invalid_token_handler(request: Request, exc: InvalidToken):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": exc.message},
        )

    @app.exception_handler(InvalidOldPassword)
    async def invalid_old_password_handler(
        request: Request, exc: InvalidOldPassword
    ):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": exc.message},
        )
