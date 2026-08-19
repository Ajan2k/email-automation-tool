from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.connection import get_db
from app.email.renderer import contact_variables, render
from app.models import Contact, Template, User
from app.schemas.template import TemplateCreate, TemplateOut, TemplatePreviewRequest, TemplateUpdate

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.get("", response_model=list[TemplateOut])
def list_templates(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.execute(
        select(Template).where(Template.owner_id == user.id).order_by(Template.id.desc())
    ).scalars().all()


@router.post("", response_model=TemplateOut, status_code=201)
def create_template(
    data: TemplateCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    template = Template(owner_id=user.id, **data.model_dump())
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.get("/{template_id}", response_model=TemplateOut)
def get_template(template_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    template = db.get(Template, template_id)
    if template is None or template.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.patch("/{template_id}", response_model=TemplateOut)
def update_template(
    template_id: int,
    data: TemplateUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    template = db.get(Template, template_id)
    if template is None or template.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Template not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(template, field, value)
    db.commit()
    db.refresh(template)
    return template


@router.post("/{template_id}/preview")
def preview_template(
    template_id: int,
    data: TemplatePreviewRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    template = db.get(Template, template_id)
    if template is None or template.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Template not found")

    if data.contact_id:
        contact = db.get(Contact, data.contact_id)
        if contact is None or contact.owner_id != user.id:
            raise HTTPException(status_code=404, detail="Contact not found")
        variables = contact_variables(contact, contact.company, user)
    else:
        sender = user.full_name.strip() if (user and user.full_name) else "InfiniteTechAI Team"
        variables = {
            "first_name": "Sarah",
            "last_name": "Chen",
            "full_name": "Sarah Chen",
            "company_name": "ABC AI",
            "job_title": "CTO",
            "website": "https://abc.ai",
            "industry": "Artificial Intelligence",
            "country": "Canada",
            "company_size": "1001-5000",
            "skills": "machine learning;product strategy",
            "phone": "+14165550100",
            "email": "sarah@abc.ai",
            "sender_name": sender,
            "from_name": sender,
            "owner_name": sender,
            "your_name": sender,
            "name": sender,
        }
    return {
        "subject": render(template.subject, variables),
        "body": render(template.body, variables),
    }


@router.delete("/{template_id}", status_code=204)
def delete_template(template_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    template = db.get(Template, template_id)
    if template is None or template.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Template not found")
    db.delete(template)
    db.commit()
