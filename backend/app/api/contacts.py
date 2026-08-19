from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.connection import get_db
from app.models import Company, Contact, User
from app.schemas.contact import ContactCreate, ContactOut, ContactUpdate, PaginatedContacts
from app.utils.email_validation import normalize_email

router = APIRouter(prefix="/api/contacts", tags=["contacts"])


@router.get("", response_model=PaginatedContacts)
def list_contacts(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    search: str = "",
    industry: str = "",
    status: str = "",
    company_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Contact).where(Contact.owner_id == user.id)
    if search:
        like = f"%{search}%"
        stmt = stmt.where(
            or_(
                Contact.email.ilike(like),
                Contact.first_name.ilike(like),
                Contact.last_name.ilike(like),
                Contact.job_title.ilike(like),
            )
        )
    if industry:
        stmt = stmt.where(Contact.industry.ilike(f"%{industry}%"))
    if status:
        stmt = stmt.where(Contact.status == status)
    if company_id:
        stmt = stmt.where(Contact.company_id == company_id)

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar() or 0
    items = db.execute(
        stmt.order_by(Contact.id.desc()).offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()
    return PaginatedContacts(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=ContactOut, status_code=201)
def create_contact(
    data: ContactCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    email = normalize_email(data.email)
    exists = db.execute(
        select(Contact).where(Contact.owner_id == user.id, Contact.email == email)
    ).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=409, detail="Contact already exists")

    company = None
    if data.company_name:
        company = db.execute(
            select(Company).where(Company.owner_id == user.id, Company.name == data.company_name)
        ).scalar_one_or_none()
        if company is None:
            company = Company(owner_id=user.id, name=data.company_name, industry=data.industry)
            db.add(company)
            db.flush()

    contact = Contact(
        owner_id=user.id,
        company_id=company.id if company else None,
        email=email,
        first_name=data.first_name,
        last_name=data.last_name,
        job_title=data.job_title,
        website=data.website,
        linkedin=data.linkedin,
        industry=data.industry,
        tags=data.tags,
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


@router.get("/{contact_id}", response_model=ContactOut)
def get_contact(contact_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    contact = db.get(Contact, contact_id)
    if contact is None or contact.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.patch("/{contact_id}", response_model=ContactOut)
def update_contact(
    contact_id: int,
    data: ContactUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    contact = db.get(Contact, contact_id)
    if contact is None or contact.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Contact not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(contact, field, value)
    db.commit()
    db.refresh(contact)
    return contact


@router.delete("/{contact_id}", status_code=204)
def delete_contact(contact_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    contact = db.get(Contact, contact_id)
    if contact is None or contact.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Contact not found")
    db.delete(contact)
    db.commit()
