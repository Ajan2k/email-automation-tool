"""LLM reply drafting with strict human-in-the-loop rules.

The LLM NEVER sends anything. It only produces a draft that a human must
review, optionally edit, and explicitly approve before it is queued.
"""
import json
import logging
import uuid
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import (
    AIReplyDraft,
    AIReplyStatus,
    Contact,
    Conversation,
    ConversationClassification,
    EmailDirection,
    EmailMessage,
    EmailStatus,
)
from app.queue.producer import enqueue_send_email

logger = logging.getLogger(__name__)

# Messages containing these topics are ALWAYS flagged for human attention.
SENSITIVE_KEYWORDS = [
    "legal", "lawyer", "contract", "pricing", "price", "refund", "complaint",
    "lawsuit", "gdpr", "security", "unsubscribe", "remove me", "stop emailing",
]

SYSTEM_PROMPT = """You are an email assistant drafting replies for a human to review.
Rules you MUST follow:
- Use only facts present in the conversation context. Never invent facts.
- Never make pricing commitments, legal statements, or promises.
- Never claim attachments or documents exist.
- Maintain a professional, concise, friendly tone.
- If the sender asks to unsubscribe, the draft must acknowledge and confirm removal.
- If the request involves legal, pricing, contracts, refunds, complaints, or security,
  set requires_human_attention to true.

Respond ONLY with JSON:
{
  "classification": "interested|meeting_request|question|not_interested|unsubscribe|needs_human",
  "draft_reply": "the reply body as plain text",
  "reason": "one sentence explaining your classification",
  "requires_human_attention": true|false
}"""


def _build_context(db: Session, conversation: Conversation) -> str:
    contact = db.get(Contact, conversation.contact_id)
    messages = db.execute(
        select(EmailMessage)
        .where(EmailMessage.conversation_id == conversation.id)
        .order_by(EmailMessage.id)
    ).scalars().all()

    lines = [
        f"Contact: {contact.first_name} {contact.last_name} <{contact.email}>",
        f"Job title: {contact.job_title}",
        f"Company: {contact.company.name if contact.company else 'unknown'}",
        "",
        "Conversation so far:",
    ]
    for m in messages:
        who = "US" if m.direction == EmailDirection.OUTBOUND else "THEM"
        lines.append(f"--- {who} ({m.created_at}) ---\nSubject: {m.subject}\n{m.body}\n")
    return "\n".join(lines)


def _call_llm(context: str) -> dict:
    response = httpx.post(
        f"{settings.llm_base_url}/chat/completions",
        headers={"Authorization": f"Bearer {settings.llm_api_key}"},
        json={
            "model": settings.llm_model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": context},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.4,
        },
        timeout=60,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    return json.loads(content)


def _keyword_flag(text: str) -> bool:
    lower = text.lower()
    return any(k in lower for k in SENSITIVE_KEYWORDS)


def generate_draft(db: Session, conversation: Conversation) -> AIReplyDraft:
    context = _build_context(db, conversation)

    last_inbound = db.execute(
        select(EmailMessage)
        .where(
            EmailMessage.conversation_id == conversation.id,
            EmailMessage.direction == EmailDirection.INBOUND,
        )
        .order_by(EmailMessage.id.desc())
    ).scalars().first()

    try:
        result = _call_llm(context)
    except Exception:
        logger.exception("LLM call failed for conversation %s", conversation.id)
        result = {
            "classification": "needs_human",
            "draft_reply": "",
            "reason": "LLM unavailable — write this reply manually.",
            "requires_human_attention": True,
        }

    requires_human = bool(result.get("requires_human_attention")) or (
        _keyword_flag(last_inbound.body if last_inbound else "")
    )

    draft = AIReplyDraft(
        owner_id=conversation.owner_id,
        conversation_id=conversation.id,
        in_reply_to_email_id=last_inbound.id if last_inbound else None,
        status=AIReplyStatus.DRAFT,
        classification=result.get("classification", "needs_human"),
        draft_subject=f"Re: {conversation.subject}" if not conversation.subject.lower().startswith("re:") else conversation.subject,
        draft_body=result.get("draft_reply", ""),
        reason=result.get("reason", ""),
        requires_human_attention=str(requires_human).lower(),
    )
    db.add(draft)

    mapping = {
        "interested": ConversationClassification.INTERESTED,
        "meeting_request": ConversationClassification.MEETING_REQUEST,
        "question": ConversationClassification.QUESTION,
        "not_interested": ConversationClassification.NOT_INTERESTED,
        "unsubscribe": ConversationClassification.UNSUBSCRIBE,
        "needs_human": ConversationClassification.NEEDS_HUMAN,
    }
    conversation.classification = mapping.get(
        draft.classification, ConversationClassification.NEEDS_HUMAN
    )
    db.commit()
    db.refresh(draft)
    return draft


def approve_and_queue(db: Session, draft: AIReplyDraft) -> EmailMessage:
    """Human approved the draft → create outbound email and enqueue it."""
    conversation = db.get(Conversation, draft.conversation_id)
    contact = db.get(Contact, conversation.contact_id)
    last_inbound = (
        db.get(EmailMessage, draft.in_reply_to_email_id) if draft.in_reply_to_email_id else None
    )

    body = draft.edited_body or draft.draft_body
    email = EmailMessage(
        owner_id=draft.owner_id,
        contact_id=contact.id,
        campaign_id=conversation.campaign_id,
        conversation_id=conversation.id,
        direction=EmailDirection.OUTBOUND,
        status=EmailStatus.QUEUED,
        subject=draft.draft_subject,
        body=body.replace("\n", "<br>\n"),
        from_email=settings.smtp_from_email,
        to_email=contact.email,
        in_reply_to=last_inbound.message_id_header if last_inbound else "",
        references=(
            f"{last_inbound.references} {last_inbound.message_id_header}".strip()
            if last_inbound
            else ""
        ),
        tracking_id=uuid.uuid4().hex,
    )
    db.add(email)
    draft.status = AIReplyStatus.APPROVED
    draft.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(email)

    enqueue_send_email(email.id)
    return email
