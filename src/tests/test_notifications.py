import pytest
from exceptions.notifications import TemplateRenderException
from models import NotificationStatus, NotificationType
from repositories.notifications import NotificationRepository
from services.notification_templates import get_subject, render_template
from services.notifications import NotificationService


@pytest.mark.asyncio
async def test_create_notification_log(db_session):
    repository = NotificationRepository(db_session)
    log = await repository.create(
        recipient_email="user@example.com",
        notification_type=NotificationType.ACTIVATION,
        subject="Activate your account",
        context={"activation_link": "https://example.com/activate/123"},
    )

    assert log.id is not None
    assert log.recipient_email == "user@example.com"
    assert log.status == NotificationStatus.PENDING


@pytest.mark.asyncio
async def test_get_by_id_returns_none_when_missing(db_session):
    repository = NotificationRepository(db_session)
    log = await repository.get_by_id(999999)

    assert log is None


@pytest.mark.asyncio
async def test_mark_sent_updates_status(db_session):
    repository = NotificationRepository(db_session)
    log = await repository.create(
        recipient_email="user@example.com",
        notification_type=NotificationType.PASSWORD_RESET,
        subject="Reset your password",
        context={"reset_link": "https://example.com/reset/123"},
    )

    await repository.mark_sent(log.id)
    updated = await repository.get_by_id(log.id)

    assert updated.status == NotificationStatus.SENT
    assert updated.sent_at is not None
    assert updated.attempts == 1


@pytest.mark.asyncio
async def test_mark_failed_updates_status(db_session):
    repository = NotificationRepository(db_session)
    log = await repository.create(
        recipient_email="user@example.com",
        notification_type=NotificationType.PASSWORD_RESET,
        subject="Reset your password",
        context={"reset_link": "https://example.com/reset/123"},
    )

    await repository.mark_failed(log.id, "SMTP timeout")
    updated = await repository.get_by_id(log.id)

    assert updated.status == NotificationStatus.FAILED
    assert updated.error_message == "SMTP timeout"


@pytest.mark.asyncio
async def test_register_notification_via_service(db_session):
    service = NotificationService(db_session)
    log = await service.register_notification(
        recipient_email="user@example.com",
        notification_type=NotificationType.COMMENT_LIKE,
        context={
            "movie_title": "Inception",
            "comment_text": "Great movie!",
            "movie_link": "https://example.com/movies/inception",
        },
    )

    assert log.status == NotificationStatus.PENDING
    assert log.subject == get_subject(NotificationType.COMMENT_LIKE)


def test_render_activation_template():
    html = render_template(
        NotificationType.ACTIVATION,
        {
            "user_name": "Bob",
            "activation_link": "https://example.com/activate/xyz",
        },
    )

    assert "Bob" in html
    assert "https://example.com/activate/xyz" in html


def test_render_template_missing_context_raises():
    with pytest.raises(TemplateRenderException):
        render_template(NotificationType.ACTIVATION, {})


def test_get_subject_for_every_type():
    for notification_type in NotificationType:
        assert isinstance(get_subject(notification_type), str)
