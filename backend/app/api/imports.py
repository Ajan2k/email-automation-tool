from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.connection import get_db
from app.models import ImportJob, User
from app.services.import_service import run_import, validate_rows
from app.utils.excel_parser import ALLOWED_EXTENSIONS, parse_contact_file

router = APIRouter(prefix="/api/imports", tags=["imports"])


def _check_extension(filename: str) -> None:
    if not any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise HTTPException(status_code=422, detail="Only .xlsx and .csv files are supported")


@router.post("/preview")
async def preview_import(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _check_extension(file.filename or "")
    content = await file.read()
    try:
        rows = parse_contact_file(file.filename or "upload.csv", content)
        preview = validate_rows(db, user.id, rows)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {
        "filename": file.filename,
        "total": preview.total,
        "valid": preview.valid,
        "invalid": preview.invalid,
        "duplicates": preview.duplicates,
        "sample_rows": preview.rows,
        "errors": preview.errors[:50],
    }


@router.post("/run")
async def execute_import(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _check_extension(file.filename or "")
    content = await file.read()
    job = run_import(db, user.id, file.filename or "upload.csv", content)
    return {
        "job_id": job.id,
        "status": job.status,
        "total": job.total_rows,
        "imported": job.imported_rows,
        "invalid": job.invalid_rows,
        "duplicates": job.duplicate_rows,
        "error": job.error,
    }


@router.get("")
def list_imports(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    jobs = db.execute(
        select(ImportJob).where(ImportJob.owner_id == user.id).order_by(ImportJob.id.desc())
    ).scalars().all()
    return [
        {
            "id": j.id,
            "filename": j.filename,
            "status": j.status,
            "total": j.total_rows,
            "imported": j.imported_rows,
            "invalid": j.invalid_rows,
            "duplicates": j.duplicate_rows,
            "created_at": j.created_at,
        }
        for j in jobs
    ]
