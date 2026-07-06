from exceptions.notifications import TemplateRenderException
from models import NotificationType


def get_subject(notification_type: NotificationType) -> str:
    subjects = {
        NotificationType.ACTIVATION: "Activate your Online Cinema account",
        NotificationType.RESEND_ACTIVATION: "Your new activation link",
        NotificationType.PASSWORD_RESET: "Reset your password",
        NotificationType.ORDER_PAYMENT_CONFIRMATION: "Your order has been paid",
        NotificationType.COMMENT_REPLY: "Someone replied to your comment",
        NotificationType.COMMENT_LIKE: "Your comment got a like",
        NotificationType.MODERATOR_MOVIE_DELETE_WARNING: (
            "Movie deletion blocked: active purchases/carts exist"
        ),
    }
    return subjects[notification_type]


def _require(context: dict, *keys: str) -> None:
    missing = [key for key in keys if key not in context]
    if missing:
        raise TemplateRenderException(f"missing context fields: {missing}")


def render_template(
    notification_type: NotificationType, context: dict
) -> str:
    if notification_type == NotificationType.ACTIVATION:
        _require(context, "activation_link")
        name = context.get("user_name", "")
        return (
            f"<p>Hi {name},</p>"
            f"<p>Please activate your account:</p>"
            f'<p><a href="{context["activation_link"]}">Activate my account</a></p>'
            f"<p>This link expires in 24 hours.</p>"
        )

    if notification_type == NotificationType.RESEND_ACTIVATION:
        _require(context, "activation_link")
        name = context.get("user_name", "")
        return (
            f"<p>Hi {name},</p>"
            f"<p>Here is your new activation link:</p>"
            f'<p><a href="{context["activation_link"]}">Activate my account</a></p>'
        )

    if notification_type == NotificationType.PASSWORD_RESET:
        _require(context, "reset_link")
        name = context.get("user_name", "")
        return (
            f"<p>Hi {name},</p>"
            f"<p>Reset your password:</p>"
            f'<p><a href="{context["reset_link"]}">Reset my password</a></p>'
        )

    if notification_type == NotificationType.ORDER_PAYMENT_CONFIRMATION:
        _require(
            context, "order_id", "movie_titles", "total_amount", "payment_date"
        )
        name = context.get("user_name", "")
        titles = "".join(f"<li>{t}</li>" for t in context["movie_titles"])
        return (
            f"<p>Hi {name},</p>"
            f'<p>Your payment for order #{context["order_id"]} was successful.</p>'
            f"<ul>{titles}</ul>"
            f'<p>Total paid: ${context["total_amount"]:.2f}</p>'
            f'<p>Date: {context["payment_date"]}</p>'
        )

    if notification_type == NotificationType.COMMENT_REPLY:
        _require(
            context, "movie_title", "original_comment", "reply_text", "movie_link"
        )
        name = context.get("user_name", "")
        return (
            f"<p>Hi {name},</p>"
            f'<p>Someone replied to your comment on {context["movie_title"]}:</p>'
            f'<p>&ldquo;{context["original_comment"]}&rdquo;</p>'
            f'<p>Reply: &ldquo;{context["reply_text"]}&rdquo;</p>'
            f'<p><a href="{context["movie_link"]}">View conversation</a></p>'
        )

    if notification_type == NotificationType.COMMENT_LIKE:
        _require(context, "movie_title", "comment_text", "movie_link")
        name = context.get("user_name", "")
        return (
            f"<p>Hi {name},</p>"
            f'<p>Your comment on {context["movie_title"]} got a like:</p>'
            f'<p>&ldquo;{context["comment_text"]}&rdquo;</p>'
            f'<p><a href="{context["movie_link"]}">View comment</a></p>'
        )

    if notification_type == NotificationType.MODERATOR_MOVIE_DELETE_WARNING:
        _require(context, "movie_title", "reason", "affected_users_count")
        name = context.get("moderator_name", "")
        return (
            f"<p>Hi {name},</p>"
            f'<p>Deletion of movie "{context["movie_title"]}" was blocked.</p>'
            f'<p>Reason: {context["reason"]}</p>'
            f'<p>Affected users: {context["affected_users_count"]}</p>'
        )

    raise TemplateRenderException(
        f"no template defined for type {notification_type}"
    )
