import logging

from app.queue.redis import get_email_queue

logger = logging.getLogger(__name__)


def enqueue_send_email(email_id: int) -> str | None:
    """Enqueue an email send job. Returns job id (or None if Redis is down —
    the scheduler will pick the email up again because it stays QUEUED)."""
    try:
        job = get_email_queue().enqueue(
            "app.queue.tasks.send_email_task",
            email_id,
            retry=None,
            job_timeout=120,
        )
        logger.info("enqueued email", extra={"email_id": email_id, "job_id": job.id})
        return job.id
    except Exception:
        logger.exception("failed to enqueue email", extra={"email_id": email_id})
        return None
