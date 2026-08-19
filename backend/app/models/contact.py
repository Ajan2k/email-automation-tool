import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ContactStatus(str, enum.Enum):
    ACTIVE = "active"
    UNSUBSCRIBED = "unsubscribed"
    BOUNCED = "bounced"
    SUPPRESSED = "suppressed"


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"), index=True, nullable=True)
    import_job_id: Mapped[int | None] = mapped_column(ForeignKey("import_jobs.id"), nullable=True)

    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(255), default="")
    last_name: Mapped[str] = mapped_column(String(255), default="")
    full_name: Mapped[str] = mapped_column(String(255), default="", index=True)
    gender: Mapped[str] = mapped_column(String(16), default="")
    job_title: Mapped[str] = mapped_column(String(255), default="", index=True)
    company_size: Mapped[str] = mapped_column(String(32), default="", index=True)
    website: Mapped[str] = mapped_column(String(255), default="")
    linkedin: Mapped[str] = mapped_column(String(255), default="")
    industry: Mapped[str] = mapped_column(String(255), default="", index=True)
    country: Mapped[str] = mapped_column(String(128), default="", index=True)
    phone: Mapped[str] = mapped_column(String(64), default="")
    skills: Mapped[str] = mapped_column(String(2048), default="")  # semicolon-separated
    tags: Mapped[str] = mapped_column(String(1024), default="")  # comma-separated
    status: Mapped[ContactStatus] = mapped_column(
        Enum(ContactStatus, native_enum=False), default=ContactStatus.ACTIVE, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    company = relationship("Company", back_populates="contacts")
