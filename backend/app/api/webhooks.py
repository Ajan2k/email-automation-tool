"""Inbound webhooks: reply detection and bounce notifications from the email provider."""
import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.conversation import InboundEmailWebhook
from app.services.ai_reply_service import generate_draft
from app.services.conversation_service import process_inbound_email
from app.services.tracking_service import record_bounce

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.post("/inbound-email")
def inbound_email(payload: InboundEmailWebhook, db: Session = Depends(get_db)):
    conversation = process_inbound_email(db, payload)
    if conversation is None:
        return {"status": "ignored", "reason": "sender not recognised"}

    # MVP: draft generated inline. In production move this onto the Redis
    # queue so the webhook returns instantly even when the LLM is slow.
    draft_id = None
    try:
        draft = generate_draft(db, conversation)
        draft_id = draft.id
    except Exception:
        logger.exception("AI draft generation failed for conversation %s", conversation.id)

    return {"status": "ok", "conversation_id": conversation.id, "draft_id": draft_id}


@router.post("/bounce")
def bounce(payload: dict, db: Session = Depends(get_db)):
    email = (payload.get("email") or payload.get("recipient") or "").lower()
    hard = payload.get("type", "hard") != "soft"
    if email:
        record_bounce(db, email, hard=hard)
    return {"status": "ok"}
