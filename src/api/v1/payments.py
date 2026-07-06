from datetime import datetime
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Query,
    Request,
    status,
)
from fastapi.responses import JSONResponse

from api.dependencies import (
    get_current_admin,
    get_current_user,
    get_payment_service,
)
from exceptions.payments import InvalidOrderStatusException
from models import UserModel
from schemas.payments import (
    CheckoutSessionCreateSchema,
    CheckoutSessionResponseSchema,
    UserPaymentHistorySchema,
)
from services.payments.base_payment import IPaymentService


router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post(
    "/sessions",
    response_model=CheckoutSessionResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_checkout_session(
    payload: CheckoutSessionCreateSchema,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    payment_service: Annotated[IPaymentService, Depends(get_payment_service)],
):
    try:
        checkout_url = await payment_service.create_checkout_session(
            order_id=payload.order_id, user_id=current_user.id
        )
        return {"checkout_url": checkout_url}

    except InvalidOrderStatusException as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": str(error),
                "recommendation": (
                    "This order cannot be paid anymore. "
                    "It might be canceled or already paid. "
                    "Please check your orders history."
                ),
            },
        ) from None
    except HTTPException as error:
        if error.status_code == 500:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "message": "Payment system is currently unavailable.",
                    "recommendation": (
                        "Stripe generation failed. "
                        "Try a different payment method later "
                        "or contact support."
                    ),
                },
            ) from None
        raise error


@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(
    request: Request,
    payment_service: Annotated[IPaymentService, Depends(get_payment_service)],
    stripe_signature: Annotated[
        str | None, Header(alias="Stripe-Signature")
    ] = None,
):
    if not stripe_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stripe-Signature header is missing",
        )

    payload = await request.body()

    await payment_service.handle_webhook(
        payload=payload, sig_header=stripe_signature
    )

    return JSONResponse(
        content={"status": "success"}, status_code=status.HTTP_200_OK
    )


@router.get(
    "/history",
    response_model=list[UserPaymentHistorySchema],
    status_code=status.HTTP_200_OK,
)
async def get_payment_history(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    payment_service: Annotated[IPaymentService, Depends(get_payment_service)],
):
    return await payment_service.get_user_history(user_id=current_user.id)


@router.get(
    "/admin/list",
    response_model=list[UserPaymentHistorySchema],
    status_code=status.HTTP_200_OK,
)
async def admin_get_all_payments(
    current_admin: Annotated[UserModel, Depends(get_current_admin)],
    payment_service: Annotated[IPaymentService, Depends(get_payment_service)],
    user_id: Annotated[
        int | None, Query(description="Filter by User ID")
    ] = None,
    payment_status: Annotated[
        str | None, Query(alias="status", description="Filter by status")
    ] = None,
    start_date: Annotated[
        datetime | None, Query(description="Filter from date (YYYY-MM-DD)")
    ] = None,
    end_date: Annotated[
        datetime | None, Query(description="Filter to date (YYYY-MM-DD)")
    ] = None,
):
    return await payment_service.get_all_payments_for_admin(
        user_id=user_id,
        status=payment_status,
        start_date=start_date,
        end_date=end_date,
    )
