from typing import Annotated, Literal, Union

from models import NotificationStatus, NotificationType
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ActivationContextSchema(BaseModel):
    user_name: str | None = None
    activation_link: str


class ResendActivationContextSchema(BaseModel):
    user_name: str | None = None
    activation_link: str


class PasswordResetContextSchema(BaseModel):
    user_name: str | None = None
    reset_link: str


class OrderPaymentConfirmationContextSchema(BaseModel):
    user_name: str | None = None
    order_id: str
    movie_titles: list[str]
    total_amount: float
    payment_date: str


class CommentReplyContextSchema(BaseModel):
    user_name: str | None = None
    movie_title: str
    original_comment: str
    reply_text: str
    movie_link: str


class CommentLikeContextSchema(BaseModel):
    user_name: str | None = None
    movie_title: str
    comment_text: str
    movie_link: str


class ModeratorMovieDeleteWarningContextSchema(BaseModel):
    moderator_name: str | None = None
    movie_title: str
    reason: str
    affected_users_count: int


class _BaseNotificationRequestSchema(BaseModel):
    recipient_email: EmailStr


class ActivationRequestSchema(_BaseNotificationRequestSchema):
    type: Literal[NotificationType.ACTIVATION]
    context: ActivationContextSchema


class ResendActivationRequestSchema(_BaseNotificationRequestSchema):
    type: Literal[NotificationType.RESEND_ACTIVATION]
    context: ResendActivationContextSchema


class PasswordResetRequestSchema(_BaseNotificationRequestSchema):
    type: Literal[NotificationType.PASSWORD_RESET]
    context: PasswordResetContextSchema


class OrderPaymentConfirmationRequestSchema(_BaseNotificationRequestSchema):
    type: Literal[NotificationType.ORDER_PAYMENT_CONFIRMATION]
    context: OrderPaymentConfirmationContextSchema


class CommentReplyRequestSchema(_BaseNotificationRequestSchema):
    type: Literal[NotificationType.COMMENT_REPLY]
    context: CommentReplyContextSchema


class CommentLikeRequestSchema(_BaseNotificationRequestSchema):
    type: Literal[NotificationType.COMMENT_LIKE]
    context: CommentLikeContextSchema


class ModeratorMovieDeleteWarningRequestSchema(_BaseNotificationRequestSchema):
    type: Literal[NotificationType.MODERATOR_MOVIE_DELETE_WARNING]
    context: ModeratorMovieDeleteWarningContextSchema


NotificationRequestSchema = Annotated[
    Union[
        ActivationRequestSchema,
        ResendActivationRequestSchema,
        PasswordResetRequestSchema,
        OrderPaymentConfirmationRequestSchema,
        CommentReplyRequestSchema,
        CommentLikeRequestSchema,
        ModeratorMovieDeleteWarningRequestSchema,
    ],
    Field(discriminator="type"),
]


class NotificationResponseSchema(BaseModel):
    id: int
    recipient_email: EmailStr
    notification_type: NotificationType
    status: NotificationStatus

    model_config = ConfigDict(from_attributes=True)


class NotificationLogResponseSchema(NotificationResponseSchema):
    subject: str
    error_message: str | None
    attempts: int

    model_config = ConfigDict(from_attributes=True)
