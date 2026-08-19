from datetime import datetime

from pydantic import BaseModel


class CampaignCreate(BaseModel):
    name: str
    description: str = ""
    template_id: int
    contact_ids: list[int]
    scheduled_at: datetime | None = None
    daily_limit: int = 500
    rate_per_minute: int = 20


class CampaignOut(BaseModel):
    id: int
    name: str
    description: str
    status: str
    template_id: int | None
    scheduled_at: datetime | None
    daily_limit: int
    rate_per_minute: int
    created_at: datetime

    model_config = {"from_attributes": True}


class CampaignStats(BaseModel):
    total_contacts: int
    queued: int
    sent: int
    delivered: int
    opened: int
    clicked: int
    bounced: int
    replied: int
    failed: int
