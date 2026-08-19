import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class EventType(str, enum.Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    BOUNCED = "bounced"
    FAILED = "failed"
    UNSUBSCRIBED = "unsubscribed"
    REPLIED = "replied"


class EmailEvent(Base):
    __tablename__ = "email_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    email_id: Mapped[int] = mapped_column(ForeignKey("email_messages.id"), index=True)
    event_type: Mapped[EventType] = mapped_column(Enum(EventType, native_enum=False), index=True)
    event_metadata: Mapped[str] = mapped_column(Text, default="")  # JSON string: ip, user_agent, url…
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
