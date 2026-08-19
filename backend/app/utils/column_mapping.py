"""Normalize rows from real-world contact exports into the platform's schema.

Built for the `Decision_Makers.xlsx` layout (2,376 rows, 18 columns):

    emails, work_email, mobile_phone, phone_numbers,
    first_name, full_name, gender,
    job_title, job_company_name, job_company_size, job_company_website,
    industry, location_country, countries,
    linkedin_url, linkedin_username, linkedin_connections, skills

but tolerant of the simpler generic layout too (first_name, last_name, email,
company, job_title, website, linkedin, industry).

Key rules:
- Email preference: `work_email` (direct corporate address, 56.4% filled)
  wins over `emails` (97.9% filled, may be a semicolon-separated list —
  we take the first valid address).
- `mobile_phone` arrives as a float (e.g. 447922834305.0) → strip the ``.0``
  and prefix ``+``. Falls back to the first entry of `phone_numbers`.
- Names arrive all-lowercase → title-cased; last name derived from
  `full_name` when missing.
- Country: `location_country` preferred, first entry of `countries` as
  fallback.
- `linkedin_url` → normalized to a full https:// URL.
"""
from __future__ import annotations

import re

from app.utils.email_validation import is_valid_email, normalize_email

# source column → canonical column (single-source aliases)
COLUMN_ALIASES = {
    "job_company_name": "company",
    "job_company_website": "website",
    "job_company_size": "company_size",
    "linkedin_url": "linkedin",
    "location_country": "country",
}

_LIST_SPLIT_RE = re.compile(r"[;,]")


def _first(value: str) -> str:
    """First entry of a semicolon/comma separated list."""
    if not value:
        return ""
    return _LIST_SPLIT_RE.split(value)[0].strip()


def _title(value: str) -> str:
    value = (value or "").strip()
    # Decision_Makers exports arrive all-lowercase → title-case those only;
    # keep mixed/upper case (e.g. "ABC AI", "McDonald") untouched
    if value and value.islower():
        return value.title()
    return value


def pick_email(row: dict) -> str:
    """work_email > first valid address in `emails` > plain `email`."""
    for candidate in (
        row.get("work_email", ""),
        *(_LIST_SPLIT_RE.split(row.get("emails", "")) if row.get("emails") else []),
        row.get("email", ""),
    ):
        email = normalize_email(candidate or "")
        if is_valid_email(email):
            return email
    return normalize_email(row.get("email") or row.get("work_email") or _first(row.get("emails", "")))


def pick_phone(row: dict) -> str:
    """mobile_phone (float artifact stripped) > first of phone_numbers."""
    mobile = (row.get("mobile_phone") or "").strip()
    if mobile:
        # pandas/openpyxl float artifact: 447922834305.0 → 447922834305
        mobile = re.sub(r"\.0$", "", mobile)
        if mobile and not mobile.startswith("+"):
            mobile = f"+{mobile}"
        return mobile
    return _first(row.get("phone_numbers", ""))


def _split_name(row: dict) -> tuple[str, str]:
    first = (row.get("first_name") or "").strip()
    last = (row.get("last_name") or "").strip()
    full = (row.get("full_name") or "").strip()
    if not last and full:
        parts = full.split()
        if not first and parts:
            first = parts[0]
        if len(parts) > 1:
            last = " ".join(parts[1:])
    return _title(first), _title(last)


def _linkedin(row: dict) -> str:
    url = (row.get("linkedin_url") or row.get("linkedin") or "").strip()
    if url and not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url


def normalize_contact_row(row: dict) -> dict:
    """Map a raw parsed row (any supported layout) into canonical fields."""
    first_name, last_name = _split_name(row)
    full_name = _title(row.get("full_name", "")) or f"{first_name} {last_name}".strip()

    return {
        "email": pick_email(row),
        "first_name": first_name,
        "last_name": last_name,
        "full_name": full_name,
        "gender": (row.get("gender") or "").strip().lower(),
        "job_title": _title(row.get("job_title", "")),
        "company": _title(row.get("job_company_name") or row.get("company") or ""),
        "company_size": (row.get("job_company_size") or row.get("company_size") or "").strip(),
        "website": (row.get("job_company_website") or row.get("website") or "").strip(),
        "industry": _title(row.get("industry", "")),
        "country": _title(row.get("location_country") or _first(row.get("countries", "")) or row.get("country", "")),
        "linkedin": _linkedin(row),
        "phone": pick_phone(row),
        "skills": (row.get("skills") or "").strip(),
    }
