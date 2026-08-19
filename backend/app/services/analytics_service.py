from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.models import (
    AIReplyDraft,
    AIReplyStatus,
    Campaign,
    Contact,
    EmailDirection,
    EmailEvent,
    EmailMessage,
    EventType,
)


def _count_events(db: Session, owner_id: int, event_type: EventType, unique: bool = True) -> int:
    stmt = (
        select(func.count(distinct(EmailEvent.email_id)) if unique else func.count(EmailEvent.id))
        .join(EmailMessage, EmailMessage.id == EmailEvent.email_id)
        .where(EmailMessage.owner_id == owner_id, EmailEvent.event_type == event_type)
    )
    return db.execute(stmt).scalar() or 0


def dashboard_stats(db: Session, owner_id: int) -> dict:
    total_contacts = db.execute(
        select(func.count(Contact.id)).where(Contact.owner_id == owner_id)
    ).scalar() or 0
    total_campaigns = db.execute(
        select(func.count(Campaign.id)).where(Campaign.owner_id == owner_id)
    ).scalar() or 0

    sent = _count_events(db, owner_id, EventType.SENT)
    bounced = _count_events(db, owner_id, EventType.BOUNCED)
    delivered = max(sent - bounced, 0)
    opened = _count_events(db, owner_id, EventType.OPENED)
    clicked = _count_events(db, owner_id, EventType.CLICKED)
    replied = _count_events(db, owner_id, EventType.REPLIED)

    pending_reviews = db.execute(
        select(func.count(AIReplyDraft.id)).where(
            AIReplyDraft.owner_id == owner_id, AIReplyDraft.status == AIReplyStatus.DRAFT
        )
    ).scalar() or 0

    def rate(numerator: int, denominator: int) -> float:
        return round(numerator / denominator * 100, 2) if denominator else 0.0

    return {
        "total_contacts": total_contacts,
        "total_campaigns": total_campaigns,
        "emails_sent": sent,
        "emails_delivered": delivered,
        "emails_opened": opened,
        "emails_clicked": clicked,
        "emails_bounced": bounced,
        "emails_replied": replied,
        "delivery_rate": rate(delivered, sent),
        "open_rate": rate(opened, delivered),
        "click_rate": rate(clicked, delivered),
        "reply_rate": rate(replied, delivered),
        "bounce_rate": rate(bounced, sent),
        "pending_ai_reviews": pending_reviews,
    }


def campaign_stats(db: Session, campaign_id: int) -> dict:
    from app.models import CampaignContact, EmailStatus

    total_contacts = db.execute(
        select(func.count(CampaignContact.id)).where(CampaignContact.campaign_id == campaign_id)
    ).scalar() or 0

    def count_status(status: EmailStatus) -> int:
        return db.execute(
            select(func.count(EmailMessage.id)).where(
                EmailMessage.campaign_id == campaign_id,
                EmailMessage.status == status,
                EmailMessage.direction == EmailDirection.OUTBOUND,
            )
        ).scalar() or 0

    def count_event(event: EventType) -> int:
        return db.execute(
            select(func.count(distinct(EmailEvent.email_id)))
            .join(EmailMessage, EmailMessage.id == EmailEvent.email_id)
            .where(EmailMessage.campaign_id == campaign_id, EmailEvent.event_type == event)
        ).scalar() or 0

    return {
        "total_contacts": total_contacts,
        "queued": count_status(EmailStatus.QUEUED),
        "sent": count_event(EventType.SENT),
        "delivered": max(count_event(EventType.SENT) - count_event(EventType.BOUNCED), 0),
        "opened": count_event(EventType.OPENED),
        "clicked": count_event(EventType.CLICKED),
        "bounced": count_event(EventType.BOUNCED),
        "replied": count_event(EventType.REPLIED),
        "failed": count_status(EmailStatus.FAILED),
    }
