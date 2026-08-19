from datetime import datetime

from pydantic import BaseModel


class MessageOut(BaseModel):
    id: int
    direction: str
    subject: str
    body: str
    from_email: str
    to_email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationOut(BaseModel):
    id: int
    contact_id: int
    subject: str
    status: str
    classification: str
    last_message_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationDetail(ConversationOut):
    messages: list[MessageOut] = []


class AIReplyOut(BaseModel):
    id: int
    conversation_id: int
    status: str
    classification: str
    draft_subject: str
    draft_body: str
    edited_body: str
    reason: str
    requires_human_attention: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AIReplyUpdate(BaseModel):
    edited_body: str | None = None


class InboundEmailWebhook(BaseModel):
    """Payload for inbound email webhooks (Mailgun/SendGrid/Postmark style)."""

    from_email: str
    to_email: str
    subject: str = ""
    body: str = ""
    message_id: str = ""
    in_reply_to: str = ""
    references: str = ""
