import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class EmailStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    SENT = "sent"
    DELIVERED = "delivered"
    BOUNCED = "bounced"
    FAILED = "failed"


class EmailDirection(str, enum.Enum):
    OUTBOUND = "outbound"
    INBOUND = "inbound"


class EmailMessage(Base):
    __tablename__ = "email_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    campaign_id: Mapped[int | None] = mapped_column(ForeignKey("campaigns.id"), index=True, nullable=True)
    contact_id: Mapped[int | None] = mapped_column(ForeignKey("contacts.id"), index=True, nullable=True)
    conversation_id: Mapped[int | None] = mapped_column(
        ForeignKey("conversations.id"), index=True, nullable=True
    )

    direction: Mapped[EmailDirection] = mapped_column(
        Enum(EmailDirection), default=EmailDirection.OUTBOUND
    )
    status: Mapped[EmailStatus] = mapped_column(Enum(EmailStatus), default=EmailStatus.QUEUED, index=True)

    subject: Mapped[str] = mapped_column(String(998), default="")
    body: Mapped[str] = mapped_column(Text, default="")
    from_email: Mapped[str] = mapped_column(String(255), default="")
    to_email: Mapped[str] = mapped_column(String(255), default="", index=True)

    # Threading headers (RFC 5322) — never rely on subject matching alone
    message_id_header: Mapped[str] = mapped_column(String(998), default="", index=True)
    in_reply_to: Mapped[str] = mapped_column(String(998), default="")
    references: Mapped[str] = mapped_column(Text, default="")

    tracking_id: Mapped[str] = mapped_column(String(64), default="", unique=True, index=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str] = mapped_column(Text, default="")
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
