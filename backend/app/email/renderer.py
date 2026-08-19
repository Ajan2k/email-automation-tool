"""Render templates with {{variable}} substitution and [Your Name] bracket replacement."""
import re

VARIABLE_RE = re.compile(r"\{\{\s*([\w_]+)\s*\}\}")
BRACKET_NAME_RE = re.compile(
    r"\[\s*(your\s+name|sender\s+name|from\s+name|owner\s+name)\s*\]", re.IGNORECASE
)


def render(text: str, variables: dict[str, str]) -> str:
    if not text:
        return ""

    def replace_var(match: re.Match) -> str:
        var_name = match.group(1).lower()
        if var_name in variables:
            return str(variables[var_name])
        return match.group(0)

    result = VARIABLE_RE.sub(replace_var, text)
    sender = (
        variables.get("sender_name")
        or variables.get("from_name")
        or variables.get("owner_name")
        or ""
    )
    if sender:
        result = BRACKET_NAME_RE.sub(sender, result)
    return result


def contact_variables(contact, company=None, owner=None) -> dict[str, str]:
    from app.core.config import settings

    sender = ""
    if owner and getattr(owner, "full_name", None):
        sender = owner.full_name.strip()
    if not sender and settings.smtp_from_name:
        sender = settings.smtp_from_name.strip()
    if not sender:
        sender = "InfiniteTechAI Team"

    first_name = (contact.first_name or "").strip()
    if not first_name and getattr(contact, "full_name", None):
        first_name = contact.full_name.strip().split()[0]
    if not first_name:
        first_name = "there"

    full_name = (
        getattr(contact, "full_name", "")
        or f"{contact.first_name or ''} {contact.last_name or ''}".strip()
    )
    if not full_name:
        full_name = first_name

    company_name = ""
    if company and getattr(company, "name", None):
        company_name = company.name.strip()
    if not company_name:
        company_name = "your company"

    return {
        "first_name": first_name,
        "last_name": (contact.last_name or "").strip(),
        "full_name": full_name,
        "email": contact.email or "",
        "job_title": contact.job_title or "",
        "website": contact.website or "",
        "industry": contact.industry or "",
        "country": getattr(contact, "country", "") or "",
        "phone": getattr(contact, "phone", "") or "",
        "skills": getattr(contact, "skills", "") or "",
        "company_size": getattr(contact, "company_size", "") or "",
        "company_name": company_name,
        "sender_name": sender,
        "from_name": sender,
        "owner_name": sender,
        "your_name": sender,
        "name": sender,
    }
