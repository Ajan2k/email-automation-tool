"""Email worker + scheduler.

Runs two things:
1. An RQ worker consuming the `emails` queue (send, retry, status updates).
2. A lightweight scheduler loop (in a thread) that:
   - launches campaigns whose scheduled_at has passed
   - re-enqueues QUEUED emails that were never picked up (Redis blip)
   - schedules due follow-up steps

Run locally:   python -m worker.main
On Render:     Background Worker service with the same command.
"""
import logging
import threading
import time
from datetime import datetime, timezone

from rq import Worker

from app.core.logging import setup_logging
from app.database.connection import SessionLocal, init_db
from app.queue.redis import EMAIL_QUEUE_NAME, get_redis

logger = logging.getLogger("worker")

SCHEDULER_INTERVAL_SECONDS = 60


def scheduler_loop() -> None:
    from sqlalchemy import select

    from app.models import Campaign, CampaignStatus, EmailMessage, EmailStatus
    from app.queue.producer import enqueue_send_email
    from app.services.campaign_service import launch_campaign
    from app.services.followup_service import schedule_due_followups

    while True:
        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)

            # 1. Launch due scheduled campaigns
            due = db.execute(
                select(Campaign).where(
                    Campaign.status == CampaignStatus.SCHEDULED,
                    Campaign.scheduled_at <= now,
                )
            ).scalars().all()
            for campaign in due:
                logger.info("launching scheduled campaign", extra={"campaign_id": campaign.id})
                launch_campaign(db, campaign)

            # 2. Requeue stuck QUEUED emails older than 5 minutes
            stuck = db.execute(
                select(EmailMessage).where(EmailMessage.status == EmailStatus.QUEUED).limit(200)
            ).scalars().all()
            for email in stuck:
                enqueue_send_email(email.id)

            # 3. Follow-ups
            created = schedule_due_followups(db, now)
            if created:
                logger.info("scheduled %s follow-up emails", created)
        except Exception:
            logger.exception("scheduler iteration failed")
        finally:
            db.close()
        time.sleep(SCHEDULER_INTERVAL_SECONDS)


def main() -> None:
    setup_logging()
    init_db()
    thread = threading.Thread(target=scheduler_loop, daemon=True, name="scheduler")
    thread.start()
    logger.info("scheduler thread started; starting RQ worker on queue %s", EMAIL_QUEUE_NAME)
    worker = Worker([EMAIL_QUEUE_NAME], connection=get_redis())
    worker.work(with_scheduler=True)


if __name__ == "__main__":
    main()
