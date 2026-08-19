"""RQ task functions executed by the worker process."""
import logging
from datetime import datetime, timezone

from app.database.connection import SessionLocal
from app.core.config import settings
from app.email.providers.smtp_provider import get_provider
from app.models import EmailEvent, EmailMessage, EmailStatus, EventType

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


def send_email_task(email_id: int) -> None:
    db = SessionLocal()
    try:
        email = db.get(EmailMessage, email_id)
        if email is None:
            logger.warning("email not found", extra={"email_id": email_id})
            return
        if email.status not in (EmailStatus.QUEUED, EmailStatus.PROCESSING):
            logger.info("email already handled", extra={"email_id": email_id})
            return

        email.status = EmailStatus.PROCESSING
        db.commit()

        try:
            provider = get_provider()
            message_id = provider.send(
                from_email=settings.smtp_from_email,
                from_name=settings.smtp_from_name,
                to_email=email.to_email,
                subject=email.subject,
                html_body=email.body,
                in_reply_to=email.in_reply_to or None,
                references=email.references or None,
            )
            email.message_id_header = message_id
            email.status = EmailStatus.SENT
            email.sent_at = datetime.now(timezone.utc)
            db.add(EmailEvent(email_id=email.id, event_type=EventType.SENT))
            db.commit()
            logger.info("email sent", extra={"email_id": email.id, "campaign_id": email.campaign_id})
        except Exception as exc:
            email.retry_count += 1
            email.error = str(exc)[:2000]
            if email.retry_count >= MAX_RETRIES:
                email.status = EmailStatus.FAILED
                db.add(EmailEvent(email_id=email.id, event_type=EventType.FAILED))
            else:
                email.status = EmailStatus.QUEUED  # scheduler/worker will retry
            db.commit()
            logger.exception("email send failed", extra={"email_id": email.id})
    finally:
        db.close()
