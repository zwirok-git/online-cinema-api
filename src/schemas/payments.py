from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from src.models import PaymentStatus


class PaymentItemBaseSchema(BaseModel):
    order_item_id: int
    price_at_payment: Decimal = Field(max_digits=10, decimal_places=2)


class PaymentItemResponseSchema(PaymentItemBaseSchema):
    id: int
    payment_id: int

    model_config = ConfigDict(from_attributes=True)


class PaymentCreateSchema(BaseModel):
    order_id: int


class PaymentResponseSchema(BaseModel):
    id: int
    user_id: int
    order_id: int
    amount: Decimal = Field(max_digits=10, decimal_places=2)
    status: PaymentStatus
    external_payment_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentDetailResponseSchema(PaymentResponseSchema):
    items: list[PaymentItemResponseSchema] = []


class StripeSessionCreateResponseSchema(BaseModel):
    payment_id: int
    checkout_url: str
