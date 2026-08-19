from datetime import datetime

from pydantic import BaseModel


class TemplateCreate(BaseModel):
    name: str
    subject: str
    body: str


class TemplateUpdate(BaseModel):
    name: str | None = None
    subject: str | None = None
    body: str | None = None


class TemplateOut(BaseModel):
    id: int
    name: str
    subject: str
    body: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TemplatePreviewRequest(BaseModel):
    contact_id: int | None = None
