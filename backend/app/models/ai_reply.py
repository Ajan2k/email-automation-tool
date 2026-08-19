import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class AIReplyStatus(str, enum.Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    REJECTED = "rejected"
    SENT = "sent"


class AIReplyDraft(Base):
    __tablename__ = "ai_reply_drafts"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), index=True)
    in_reply_to_email_id: Mapped[int | None] = mapped_column(
        ForeignKey("email_messages.id"), nullable=True
    )

    status: Mapped[AIReplyStatus] = mapped_column(
        Enum(AIReplyStatus), default=AIReplyStatus.DRAFT, index=True
    )
    classification: Mapped[str] = mapped_column(String(64), default="")
    draft_subject: Mapped[str] = mapped_column(String(998), default="")
    draft_body: Mapped[str] = mapped_column(Text, default="")
    edited_body: Mapped[str] = mapped_column(Text, default="")
    reason: Mapped[str] = mapped_column(Text, default="")
    requires_human_attention: Mapped[str] = mapped_column(String(8), default="false")
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
