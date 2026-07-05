from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from services.exceptions import (
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
