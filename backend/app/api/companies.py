from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.connection import get_db
from app.models import Company, User
from app.schemas.company import CompanyCreate, CompanyOut

router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.get("", response_model=list[CompanyOut])
def list_companies(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.execute(
        select(Company).where(Company.owner_id == user.id).order_by(Company.name)
    ).scalars().all()


@router.post("", response_model=CompanyOut, status_code=201)
def create_company(
    data: CompanyCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    company = Company(owner_id=user.id, **data.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.delete("/{company_id}", status_code=204)
def delete_company(company_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    company = db.get(Company, company_id)
    if company is None or company.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Company not found")
    db.delete(company)
    db.commit()
