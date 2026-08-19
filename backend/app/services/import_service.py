"""Excel/CSV → column mapping → validated preview → bulk insert into PostgreSQL.

Supports both the generic layout (first_name, last_name, email, company, …)
and the Decision_Makers.xlsx layout (work_email, emails, job_company_name,
linkedin_url, location_country, skills, …) via app.utils.column_mapping.
"""
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, Contact, ImportJob, ImportStatus
from app.utils.column_mapping import normalize_contact_row
from app.utils.email_validation import is_valid_email
from app.utils.excel_parser import parse_contact_file


@dataclass
class ImportPreview:
    total: int = 0
    valid: int = 0
    invalid: int = 0
    duplicates: int = 0
    rows: list[dict] = field(default_factory=list)  # first N valid rows for preview
    errors: list[dict] = field(default_factory=list)


def _existing_emails(db: Session, owner_id: int) -> set[str]:
    return {
        e[0]
        for e in db.execute(select(Contact.email).where(Contact.owner_id == owner_id)).all()
    }


def validate_rows(db: Session, owner_id: int, rows: list[dict]) -> ImportPreview:
    preview = ImportPreview(total=len(rows))
    existing = _existing_emails(db, owner_id)
    seen_in_file: set[str] = set()

    for idx, raw in enumerate(rows, start=2):  # header is row 1
        row = normalize_contact_row(raw)
        email = row["email"]
        if not is_valid_email(email):
            preview.invalid += 1
            source = raw.get("work_email") or raw.get("emails") or raw.get("email") or ""
            preview.errors.append({"row": idx, "error": f"No valid email found: {source!r}"})
            continue
        if email in existing or email in seen_in_file:
            preview.duplicates += 1
            continue
        seen_in_file.add(email)
        preview.valid += 1
        if len(preview.rows) < 20:
            preview.rows.append(row)

    return preview


def run_import(db: Session, owner_id: int, filename: str, content: bytes) -> ImportJob:
    job = ImportJob(owner_id=owner_id, filename=filename, status=ImportStatus.PENDING)
    db.add(job)
    db.flush()

    try:
        rows = parse_contact_file(filename, content)
        preview = validate_rows(db, owner_id, rows)
        job.total_rows = preview.total
        job.valid_rows = preview.valid
        job.invalid_rows = preview.invalid
        job.duplicate_rows = preview.duplicates

        company_cache: dict[str, Company] = {}
        existing = _existing_emails(db, owner_id)
        imported = 0
        for raw in rows:
            row = normalize_contact_row(raw)
            email = row["email"]
            if not is_valid_email(email) or email in existing:
                continue
            existing.add(email)

            company = None
            company_name = row["company"]
            if company_name:
                key = company_name.lower()
                company = company_cache.get(key)
                if company is None:
                    company = db.execute(
                        select(Company).where(
                            Company.owner_id == owner_id, Company.name == company_name
                        )
                    ).scalar_one_or_none()
                    if company is None:
                        company = Company(
                            owner_id=owner_id,
                            name=company_name,
                            website=row["website"],
                            industry=row["industry"],
                        )
                        db.add(company)
                        db.flush()
                    company_cache[key] = company

            db.add(
                Contact(
                    owner_id=owner_id,
                    import_job_id=job.id,
                    company_id=company.id if company else None,
                    email=email,
                    first_name=row["first_name"],
                    last_name=row["last_name"],
                    full_name=row["full_name"],
                    gender=row["gender"],
                    job_title=row["job_title"],
                    company_size=row["company_size"],
                    website=row["website"],
                    linkedin=row["linkedin"],
                    industry=row["industry"],
                    country=row["country"],
                    phone=row["phone"],
                    skills=row["skills"],
                )
            )
            imported += 1

        job.imported_rows = imported
        job.status = ImportStatus.COMPLETED
        db.commit()
    except Exception as exc:
        db.rollback()
        job = db.get(ImportJob, job.id) or job
        job.status = ImportStatus.FAILED
        job.error = str(exc)[:2000]
        db.add(job)
        db.commit()

    return job
