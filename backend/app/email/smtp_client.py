"""Backwards-compatible import point. Use app.email.providers going forward."""
from app.email.providers.smtp_provider import SMTPProvider, get_provider  # noqa: F401
