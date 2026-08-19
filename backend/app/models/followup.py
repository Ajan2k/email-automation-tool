import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class FollowupSequence(Base):
    __tablename__ = "followup_sequences"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    campaign_id: Mapped[int | None] = mapped_column(ForeignKey("campaigns.id"), index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    steps = relationship("FollowupStep", back_populates="sequence", order_by="FollowupStep.order")


class FollowupStep(Base):
    __tablename__ = "followup_steps"

    id: Mapped[int] = mapped_column(primary_key=True)
    sequence_id: Mapped[int] = mapped_column(ForeignKey("followup_sequences.id"), index=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("templates.id"))
    order: Mapped[int] = mapped_column(Integer, default=1)
    delay_days: Mapped[int] = mapped_column(Integer, default=3)  # days after previous step

    sequence = relationship("FollowupSequence", back_populates="steps")
