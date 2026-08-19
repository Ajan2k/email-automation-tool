"""Excel/CSV → validated preview → bulk insert into PostgreSQL."""
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, Contact, ImportJob, ImportStatus
from app.utils.email_validation import is_valid_email, normalize_email
from app.utils.excel_parser import parse_contact_file


@dataclass
class ImportPreview:
    total: int = 0
    valid: int = 0
    invalid: int = 0
    duplicates: int = 0
    rows: list[dict] = field(default_factory=list)  # first N valid rows for preview
    errors: list[dict] = field(default_factory=list)


def validate_rows(db: Session, owner_id: int, rows: list[dict]) -> ImportPreview:
    preview = ImportPreview(total=len(rows))
    existing = {
        e[0]
        for e in db.execute(select(Contact.email).where(Contact.owner_id == owner_id)).all()
    }
    seen_in_file: set[str] = set()

    for idx, row in enumerate(rows, start=2):  # header is row 1
        email = normalize_email(row.get("email", ""))
        if not is_valid_email(email):
            preview.invalid += 1
            preview.errors.append({"row": idx, "error": f"Invalid email: {row.get('email', '')!r}"})
            continue
        if email in existing or email in seen_in_file:
            preview.duplicates += 1
            continue
        seen_in_file.add(email)
        preview.valid += 1
        if len(preview.rows) < 20:
            preview.rows.append({**row, "email": email})

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
        existing = {
            e[0]
            for e in db.execute(select(Contact.email).where(Contact.owner_id == owner_id)).all()
        }
        imported = 0
        for row in rows:
            email = normalize_email(row.get("email", ""))
            if not is_valid_email(email) or email in existing:
                continue
            existing.add(email)

            company = None
            company_name = (row.get("company") or "").strip()
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
                            website=row.get("website", ""),
                            industry=row.get("industry", ""),
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
                    first_name=row.get("first_name", ""),
                    last_name=row.get("last_name", ""),
                    job_title=row.get("job_title", ""),
                    website=row.get("website", ""),
                    linkedin=row.get("linkedin", ""),
                    industry=row.get("industry", ""),
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
