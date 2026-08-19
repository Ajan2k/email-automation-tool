import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, make_msgid

from app.core.config import settings
from app.email.providers.base import EmailProvider


class SMTPProvider(EmailProvider):
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
        msg = MIMEMultipart("alternative")
        msg["From"] = formataddr((from_name, from_email))
        msg["To"] = to_email
        msg["Subject"] = subject
        msg["Message-ID"] = message_id or make_msgid()
        if in_reply_to:
            msg["In-Reply-To"] = in_reply_to
        if references:
            msg["References"] = references
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_username:
                server.login(settings.smtp_username, settings.smtp_password)
            server.sendmail(from_email, [to_email], msg.as_string())

        return msg["Message-ID"]


def get_provider() -> EmailProvider:
    return SMTPProvider()
