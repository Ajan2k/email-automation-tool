"""Follow-up scheduling. A step only fires if the contact has NOT replied,
NOT unsubscribed, and NOT hard-bounced."""
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.email.renderer import contact_variables, render
from app.models import (
    CampaignContact,
    Contact,
    ContactStatus,
    EmailDirection,
    EmailMessage,
    EmailStatus,
    FollowupSequence,
    Template,
)
from app.queue.producer import enqueue_send_email


def contact_has_replied(db: Session, contact_id: int) -> bool:
    return (
        db.execute(
            select(EmailMessage.id).where(
                EmailMessage.contact_id == contact_id,
                EmailMessage.direction == EmailDirection.INBOUND,
            )
        ).first()
        is not None
    )


def schedule_due_followups(db: Session, now: datetime | None = None) -> int:
    """Called by the scheduler loop. Creates queued follow-up emails."""
    now = now or datetime.now(timezone.utc)
    created = 0

    sequences = db.execute(
        select(FollowupSequence).where(FollowupSequence.active == True)  # noqa: E712
    ).scalars().all()

    for seq in sequences:
        if not seq.campaign_id:
            continue
        contact_ids = [
            r[0]
            for r in db.execute(
                select(CampaignContact.contact_id).where(
                    CampaignContact.campaign_id == seq.campaign_id
                )
            ).all()
        ]
        for contact_id in contact_ids:
            contact = db.get(Contact, contact_id)
            if contact is None or contact.status != ContactStatus.ACTIVE:
                continue  # unsubscribed / bounced → stop sequence
            if contact_has_replied(db, contact_id):
                continue  # replied → stop sequence

            last_outbound = db.execute(
                select(EmailMessage)
                .where(
                    EmailMessage.contact_id == contact_id,
                    EmailMessage.campaign_id == seq.campaign_id,
                    EmailMessage.direction == EmailDirection.OUTBOUND,
                    EmailMessage.status.in_([EmailStatus.SENT, EmailStatus.DELIVERED]),
                )
                .order_by(EmailMessage.id.desc())
            ).scalars().first()
            if last_outbound is None or last_outbound.sent_at is None:
                continue

            sent_count = db.execute(
                select(EmailMessage.id).where(
                    EmailMessage.contact_id == contact_id,
                    EmailMessage.campaign_id == seq.campaign_id,
                    EmailMessage.direction == EmailDirection.OUTBOUND,
                )
            ).all()
            step_index = len(sent_count) - 1  # 0 initial email → step 0 next
            steps = sorted(seq.steps, key=lambda s: s.order)
            if step_index >= len(steps):
                continue
            step = steps[step_index]

            sent_at = last_outbound.sent_at
            if sent_at.tzinfo is None:
                sent_at = sent_at.replace(tzinfo=timezone.utc)
            if now < sent_at + timedelta(days=step.delay_days):
                continue

            template = db.get(Template, step.template_id)
            if template is None:
                continue
            variables = contact_variables(contact, contact.company)
            email = EmailMessage(
                owner_id=seq.owner_id,
                campaign_id=seq.campaign_id,
                contact_id=contact.id,
                status=EmailStatus.QUEUED,
                subject=render(template.subject, variables),
                body=render(template.body, variables).replace("\n", "<br>\n"),
                from_email=settings.smtp_from_email,
                to_email=contact.email,
                tracking_id=uuid.uuid4().hex,
            )
            db.add(email)
            db.flush()
            enqueue_send_email(email.id)
            created += 1

    db.commit()
    return created
