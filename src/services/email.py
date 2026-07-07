import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from core.config import settings
from exceptions.notifications import EmailDeliveryException


def send_email(to: str, subject: str, html_body: str) -> None:
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = settings.EMAIL_FROM
    message["To"] = to
    message.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        server = smtplib.SMTP(
            settings.SMTP_HOST, settings.SMTP_PORT, timeout=10
        )
        if settings.SMTP_USE_TLS:
            server.starttls()
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.EMAIL_FROM, [to], message.as_string())
        server.quit()
    except (smtplib.SMTPException, OSError) as exc:
        raise EmailDeliveryException(str(exc)) from exc
