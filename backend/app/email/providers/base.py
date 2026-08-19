from abc import ABC, abstractmethod


class EmailProvider(ABC):
    """Abstraction so SMTP can later be swapped for SendGrid/SES/Mailgun."""

    @abstractmethod
    def send(
        self,
        *,
        from_email: str,
        from_name: str,
        to_email: str,
        subject: str,
        html_body: str,
        message_id: str | None = None,
        in_reply_to: str | None = None,
        references: str | None = None,
    ) -> str:
        """Send an email. Returns the Message-ID used."""
