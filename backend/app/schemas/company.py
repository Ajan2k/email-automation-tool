from datetime import datetime

from pydantic import BaseModel


class CompanyCreate(BaseModel):
    name: str
    website: str = ""
    industry: str = ""


class CompanyOut(BaseModel):
    id: int
    name: str
    website: str
    industry: str
    created_at: datetime

    model_config = {"from_attributes": True}
