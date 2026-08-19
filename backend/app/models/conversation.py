import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ConversationStatus(str, enum.Enum):
    OPEN = "open"
    NEEDS_REVIEW = "needs_review"
    CLOSED = "closed"


class ConversationClassification(str, enum.Enum):
    UNCLASSIFIED = "unclassified"
    INTERESTED = "interested"
    MEETING_REQUEST = "meeting_request"
    QUESTION = "question"
    NOT_INTERESTED = "not_interested"
    UNSUBSCRIBE = "unsubscribe"
    NEEDS_HUMAN = "needs_human"


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"), index=True)
    campaign_id: Mapped[int | None] = mapped_column(ForeignKey("campaigns.id"), nullable=True)

    subject: Mapped[str] = mapped_column(String(998), default="")
    status: Mapped[ConversationStatus] = mapped_column(
        Enum(ConversationStatus), default=ConversationStatus.OPEN, index=True
    )
    classification: Mapped[ConversationClassification] = mapped_column(
        Enum(ConversationClassification), default=ConversationClassification.UNCLASSIFIED
    )
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    contact = relationship("Contact")
