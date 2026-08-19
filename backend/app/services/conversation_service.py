"""Inbound reply → thread matching → conversation storage."""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Contact,
    Conversation,
    ConversationStatus,
    EmailDirection,
    EmailEvent,
    EmailMessage,
    EmailStatus,
    EventType,
)


def process_inbound_email(db: Session, payload) -> Conversation | None:
    """Match an inbound reply to a conversation using In-Reply-To / References
    headers first, then fall back to sender address."""
    original: EmailMessage | None = None

    # 1. RFC 5322 threading headers
    header_ids = [h for h in [payload.in_reply_to, *payload.references.split()] if h]
    for header_id in header_ids:
        original = db.execute(
            select(EmailMessage).where(EmailMessage.message_id_header == header_id)
        ).scalar_one_or_none()
        if original:
            break

    # 2. Fallback: most recent outbound email to this sender
    if original is None:
        original = db.execute(
            select(EmailMessage)
            .where(
                EmailMessage.to_email == payload.from_email.lower(),
                EmailMessage.direction == EmailDirection.OUTBOUND,
            )
            .order_by(EmailMessage.id.desc())
        ).scalars().first()

    contact = db.execute(
        select(Contact).where(Contact.email == payload.from_email.lower())
    ).scalars().first()
    if original is None and contact is None:
        return None  # unknown sender — not part of any campaign

    owner_id = original.owner_id if original else contact.owner_id
    contact_id = original.contact_id if original and original.contact_id else (
        contact.id if contact else None
    )
    if contact_id is None:
        return None

    conversation = None
    if original and original.conversation_id:
        conversation = db.get(Conversation, original.conversation_id)
    if conversation is None:
        conversation = db.execute(
            select(Conversation).where(
                Conversation.contact_id == contact_id,
                Conversation.status != ConversationStatus.CLOSED,
            )
        ).scalars().first()
    if conversation is None:
        conversation = Conversation(
            owner_id=owner_id,
            contact_id=contact_id,
            campaign_id=original.campaign_id if original else None,
            subject=payload.subject,
        )
        db.add(conversation)
        db.flush()

    if original is not None:
        if original.conversation_id is None:
            original.conversation_id = conversation.id
        db.add(EmailEvent(email_id=original.id, event_type=EventType.REPLIED))

    inbound = EmailMessage(
        owner_id=owner_id,
        contact_id=contact_id,
        campaign_id=original.campaign_id if original else None,
        conversation_id=conversation.id,
        direction=EmailDirection.INBOUND,
        status=EmailStatus.DELIVERED,
        subject=payload.subject,
        body=payload.body,
        from_email=payload.from_email.lower(),
        to_email=payload.to_email.lower(),
        message_id_header=payload.message_id,
        in_reply_to=payload.in_reply_to,
        references=payload.references,
    )
    db.add(inbound)
    conversation.status = ConversationStatus.NEEDS_REVIEW
    conversation.last_message_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(conversation)
    return conversation
