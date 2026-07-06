from exceptions.notifications import TemplateRenderException
from models import NotificationType


def get_subject(notification_type: NotificationType) -> str:
    subjects = {
        NotificationType.ACTIVATION: ("Activate your Online Cinema account"),
        NotificationType.RESEND_ACTIVATION: "Your new activation link",
        NotificationType.PASSWORD_RESET: "Reset your password",
        NotificationType.ORDER_PAYMENT_CONFIRMATION: (
            "Your order has been paid"
        ),
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


def render_template(notification_type: NotificationType, context: dict) -> str:
    if notification_type == NotificationType.ACTIVATION:
        _require(context, "activation_link")
        name = context.get("user_name", "")
        link = context["activation_link"]
        return (
            f"<p>Hi {name},</p>"
            f"<p>Please activate your account:</p>"
            f'<p><a href="{link}">Activate my account</a></p>'
            f"<p>This link expires in 24 hours.</p>"
        )

    if notification_type == NotificationType.RESEND_ACTIVATION:
        _require(context, "activation_link")
        name = context.get("user_name", "")
        link = context["activation_link"]
        return (
            f"<p>Hi {name},</p>"
            f"<p>Here is your new activation link:</p>"
            f'<p><a href="{link}">Activate my account</a></p>'
        )

    if notification_type == NotificationType.PASSWORD_RESET:
        _require(context, "reset_link")
        name = context.get("user_name", "")
        link = context["reset_link"]
        return (
            f"<p>Hi {name},</p>"
            f"<p>Reset your password:</p>"
            f'<p><a href="{link}">Reset my password</a></p>'
        )

    if notification_type == NotificationType.ORDER_PAYMENT_CONFIRMATION:
        _require(
            context,
            "order_id",
            "movie_titles",
            "total_amount",
            "payment_date",
        )
        name = context.get("user_name", "")
        titles = "".join(f"<li>{t}</li>" for t in context["movie_titles"])
        order_id = context["order_id"]
        total = context["total_amount"]
        date = context["payment_date"]
        return (
            f"<p>Hi {name},</p>"
            f"<p>Your payment for order #{order_id} "
            f"was successful.</p>"
            f"<ul>{titles}</ul>"
            f"<p>Total paid: ${total:.2f}</p>"
            f"<p>Date: {date}</p>"
        )

    if notification_type == NotificationType.COMMENT_REPLY:
        _require(
            context,
            "movie_title",
            "original_comment",
            "reply_text",
            "movie_link",
        )
        name = context.get("user_name", "")
        movie_title = context["movie_title"]
        original_comment = context["original_comment"]
        reply_text = context["reply_text"]
        movie_link = context["movie_link"]
        return (
            f"<p>Hi {name},</p>"
            f"<p>Someone replied to your comment on "
            f"{movie_title}:</p>"
            f"<p>&ldquo;{original_comment}&rdquo;</p>"
            f"<p>Reply: &ldquo;{reply_text}&rdquo;</p>"
            f'<p><a href="{movie_link}">View conversation</a></p>'
        )

    if notification_type == NotificationType.COMMENT_LIKE:
        _require(context, "movie_title", "comment_text", "movie_link")
        name = context.get("user_name", "")
        movie_title = context["movie_title"]
        comment_text = context["comment_text"]
        movie_link = context["movie_link"]
        return (
            f"<p>Hi {name},</p>"
            f"<p>Your comment on {movie_title} got a like:</p>"
            f"<p>&ldquo;{comment_text}&rdquo;</p>"
            f'<p><a href="{movie_link}">View comment</a></p>'
        )

    if notification_type == NotificationType.MODERATOR_MOVIE_DELETE_WARNING:
        _require(context, "movie_title", "reason", "affected_users_count")
        name = context.get("moderator_name", "")
        movie_title = context["movie_title"]
        reason = context["reason"]
        affected = context["affected_users_count"]
        return (
            f"<p>Hi {name},</p>"
            f'<p>Deletion of movie "{movie_title}" was blocked.</p>'
            f"<p>Reason: {reason}</p>"
            f"<p>Affected users: {affected}</p>"
        )

    raise TemplateRenderException(
        f"no template defined for type {notification_type}"
    )
