from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from models import PaymentStatus


# --- Схемы для позиций внутри платежа (если нужны) ---
class PaymentItemBaseSchema(BaseModel):
    order_item_id: int
    price_at_payment: Decimal = Field(max_digits=10, decimal_places=2)


class PaymentItemResponseSchema(PaymentItemBaseSchema):
    id: int
    payment_id: int

    model_config = ConfigDict(from_attributes=True)


# --- Схемы для создания сессии Stripe (Запрос / Ответ) ---
class CheckoutSessionCreateSchema(BaseModel):
    """Схема для входящего запроса на оплату заказа."""

    order_id: int


class CheckoutSessionResponseSchema(BaseModel):
    """Схема ответа: возвращает клиенту ссылку на Stripe и ID транзакции."""

    payment_id: int
    checkout_url: HttpUrl


# --- Схемы для отображения информации о платеже из БД ---
class PaymentResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    order_id: int
    amount: Decimal = Field(max_digits=10, decimal_places=2)
    status: PaymentStatus
    external_payment_id: str | None = None
    created_at: datetime
    updated_at: datetime


class PaymentDetailResponseSchema(PaymentResponseSchema):
    """Полная информация о платеже вместе с деталями заказа."""

    items: list[PaymentItemResponseSchema] = []
