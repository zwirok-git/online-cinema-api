from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import DECIMAL, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCESSFUL = "successful"
    CANCELED = "canceled"
    REFUNDED = "refunded"
    FAILED = "failed"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        String(20), default=PaymentStatus.PENDING, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    external_payment_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, index=True, nullable=True
    )
    items: Mapped[list["PaymentItem"]] = relationship(
        "PaymentItem",
        back_populates="payment",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class PaymentItem(Base):
    __tablename__ = "payment_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    payment_id: Mapped[int] = mapped_column(
        ForeignKey("payments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    order_item_id: Mapped[int] = mapped_column(
        ForeignKey("order_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    price_at_payment: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2), nullable=False
    )

    payment: Mapped["Payment"] = relationship(
        "Payment", back_populates="items"
    )
