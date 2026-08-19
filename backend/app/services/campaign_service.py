"""Campaign creation and execution: render template → create email rows → enqueue."""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.email.renderer import contact_variables, render
from app.models import (
    Campaign,
    CampaignContact,
    CampaignStatus,
    Contact,
    ContactStatus,
    EmailMessage,
    EmailStatus,
    SuppressionEntry,
    Template,
)
from app.queue.producer import enqueue_send_email


def create_campaign(db: Session, owner_id: int, data) -> Campaign:
    campaign = Campaign(
        owner_id=owner_id,
        name=data.name,
        description=data.description,
        template_id=data.template_id,
        scheduled_at=data.scheduled_at,
        daily_limit=data.daily_limit,
        rate_per_minute=data.rate_per_minute,
        status=CampaignStatus.SCHEDULED if data.scheduled_at else CampaignStatus.DRAFT,
    )
    db.add(campaign)
    db.flush()
    for contact_id in set(data.contact_ids):
        db.add(CampaignContact(campaign_id=campaign.id, contact_id=contact_id))
    db.commit()
    db.refresh(campaign)
    return campaign


def launch_campaign(db: Session, campaign: Campaign) -> int:
    """Render + queue one email per eligible contact. Returns number queued."""
    template = db.get(Template, campaign.template_id)
    if template is None:
        raise ValueError("Campaign has no template")

    suppressed = {
        s[0]
        for s in db.execute(
            select(SuppressionEntry.email).where(SuppressionEntry.owner_id == campaign.owner_id)
        ).all()
    }

    contact_ids = [
        cc[0]
        for cc in db.execute(
            select(CampaignContact.contact_id).where(CampaignContact.campaign_id == campaign.id)
        ).all()
    ]

    queued = 0
    for contact_id in contact_ids:
        contact = db.get(Contact, contact_id)
        if contact is None or contact.status != ContactStatus.ACTIVE:
            continue
        if contact.email in suppressed:
            continue

        variables = contact_variables(contact, contact.company)
        email = EmailMessage(
            owner_id=campaign.owner_id,
            campaign_id=campaign.id,
            contact_id=contact.id,
            status=EmailStatus.QUEUED,
            subject=render(template.subject, variables),
            body=_with_tracking(render(template.body, variables)),
            from_email=settings.smtp_from_email,
            to_email=contact.email,
            tracking_id=uuid.uuid4().hex,
        )
        db.add(email)
        db.flush()
        # rewrite links + append open pixel now that tracking_id exists
        email.body = _inject_tracking(email.body, email.tracking_id)
        queued += 1

    campaign.status = CampaignStatus.RUNNING
    db.commit()

    # enqueue after commit so worker can see the rows
    for email in db.execute(
        select(EmailMessage).where(
            EmailMessage.campaign_id == campaign.id, EmailMessage.status == EmailStatus.QUEUED
        )
    ).scalars():
        enqueue_send_email(email.id)

    return queued


def _with_tracking(body_html: str) -> str:
    if "<html" not in body_html.lower():
        body_html = body_html.replace("\n", "<br>\n")
    return body_html


def _inject_tracking(body_html: str, tracking_id: str) -> str:
    import re

    base = settings.public_api_url.rstrip("/")

    def rewrite_link(match: re.Match) -> str:
        url = match.group(1)
        if url.startswith(f"{base}/api/track"):
            return match.group(0)
        return f'href="{base}/api/track/click/{tracking_id}?url={url}"'

    body_html = re.sub(r'href="([^"]+)"', rewrite_link, body_html)
    pixel = f'<img src="{base}/api/track/open/{tracking_id}" width="1" height="1" alt="" style="display:none">'
    return body_html + pixel
