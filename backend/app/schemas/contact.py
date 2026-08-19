from datetime import datetime

from pydantic import BaseModel, EmailStr


class ContactCreate(BaseModel):
    email: EmailStr
    first_name: str = ""
    last_name: str = ""
    job_title: str = ""
    website: str = ""
    linkedin: str = ""
    industry: str = ""
    tags: str = ""
    company_name: str = ""


class ContactUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    job_title: str | None = None
    website: str | None = None
    linkedin: str | None = None
    industry: str | None = None
    tags: str | None = None


class ContactOut(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    job_title: str
    industry: str
    tags: str
    status: str
    company_id: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedContacts(BaseModel):
    items: list[ContactOut]
    total: int
    page: int
    page_size: int
