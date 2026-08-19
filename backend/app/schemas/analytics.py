from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_contacts: int
    total_campaigns: int
    emails_sent: int
    emails_delivered: int
    emails_opened: int
    emails_clicked: int
    emails_bounced: int
    emails_replied: int
    delivery_rate: float
    open_rate: float
    click_rate: float
    reply_rate: float
    bounce_rate: float
    pending_ai_reviews: int
