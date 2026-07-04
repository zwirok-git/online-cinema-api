from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse

from api.dependencies import get_current_user, get_stripe_payment_service
from models import UserModel
from schemas.payments import (
    CheckoutSessionCreateSchema,
    CheckoutSessionResponseSchema,
)
from services.payments import StripePaymentService


router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post(
    "/sessions",
    response_model=CheckoutSessionResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_checkout_session(
    payload: CheckoutSessionCreateSchema,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    payment_service: Annotated[
        StripePaymentService, Depends(get_stripe_payment_service)
    ],
):
    checkout_url = await payment_service.create_checkout_session(
        order_id=payload.order_id, user_id=current_user.id
    )
    return {"checkout_url": checkout_url}


@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(
    request: Request,
    payment_service: Annotated[
        StripePaymentService, Depends(get_stripe_payment_service)
    ],
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
