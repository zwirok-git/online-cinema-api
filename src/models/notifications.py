from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class NotificationType(str, Enum):
    ACTIVATION = "activation"
    RESEND_ACTIVATION = "resend_activation"
    PASSWORD_RESET = "password_reset"
    ORDER_PAYMENT_CONFIRMATION = "order_payment_confirmation"
    COMMENT_REPLY = "comment_reply"
    COMMENT_LIKE = "comment_like"
    MODERATOR_MOVIE_DELETE_WARNING = "moderator_movie_delete_warning"


class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    recipient_email: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )
    notification_type: Mapped[NotificationType] = mapped_column(
        String(50), nullable=False, index=True
    )
    status: Mapped[NotificationStatus] = mapped_column(
        String(20),
        default=NotificationStatus.PENDING,
        nullable=False,
        index=True,
    )
    context: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempts: Mapped[int] = mapped_column(default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
