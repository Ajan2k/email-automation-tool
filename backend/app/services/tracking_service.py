"""Open / click / bounce / unsubscribe event recording."""
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Contact,
    ContactStatus,
    EmailEvent,
    EmailMessage,
    EmailStatus,
    EventType,
    SuppressionEntry,
)


def _find_email(db: Session, tracking_id: str) -> EmailMessage | None:
    return db.execute(
        select(EmailMessage).where(EmailMessage.tracking_id == tracking_id)
    ).scalar_one_or_none()


def record_open(db: Session, tracking_id: str, ip: str = "", user_agent: str = "") -> None:
    email = _find_email(db, tracking_id)
    if email is None:
        return
    db.add(
        EmailEvent(
            email_id=email.id,
            event_type=EventType.OPENED,
            event_metadata=json.dumps({"ip": ip, "user_agent": user_agent}),
        )
    )
    db.commit()


def record_click(db: Session, tracking_id: str, url: str) -> None:
    email = _find_email(db, tracking_id)
    if email is None:
        return
    db.add(
        EmailEvent(
            email_id=email.id,
            event_type=EventType.CLICKED,
            event_metadata=json.dumps({"url": url}),
        )
    )
    db.commit()


def record_bounce(db: Session, to_email: str, hard: bool = True) -> None:
    email = db.execute(
        select(EmailMessage)
        .where(EmailMessage.to_email == to_email, EmailMessage.status == EmailStatus.SENT)
        .order_by(EmailMessage.id.desc())
    ).scalars().first()
    if email is not None:
        email.status = EmailStatus.BOUNCED
        db.add(EmailEvent(email_id=email.id, event_type=EventType.BOUNCED))
    if hard:
        contact = db.execute(
            select(Contact).where(Contact.email == to_email)
        ).scalars().first()
        if contact is not None:
            contact.status = ContactStatus.BOUNCED
            db.add(SuppressionEntry(owner_id=contact.owner_id, email=to_email, reason="bounce"))
    db.commit()


def record_unsubscribe(db: Session, tracking_id: str) -> None:
    email = _find_email(db, tracking_id)
    if email is None:
        return
    db.add(EmailEvent(email_id=email.id, event_type=EventType.UNSUBSCRIBED))
    contact = db.get(Contact, email.contact_id) if email.contact_id else None
    if contact is not None:
        contact.status = ContactStatus.UNSUBSCRIBED
        db.add(
            SuppressionEntry(owner_id=contact.owner_id, email=contact.email, reason="unsubscribe")
        )
    db.commit()
