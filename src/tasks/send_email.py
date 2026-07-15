from core.celery import celery
from exceptions.notifications import EmailDeliveryException
from services.email import send_email


@celery.task(
    name="send_email_task",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def send_email_task(self, to: str, subject: str, html_body: str) -> str:
    try:
        send_email(to=to, subject=subject, html_body=html_body)
        return f"Email sent to {to}."
    except EmailDeliveryException as exc:
        raise self.retry(exc=exc) from exc
