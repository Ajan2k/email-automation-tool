"""Render templates with {{variable}} substitution."""
import re

VARIABLE_RE = re.compile(r"\{\{\s*(\w+)\s*\}\}")


def render(text: str, variables: dict[str, str]) -> str:
    def replace(match: re.Match) -> str:
        return str(variables.get(match.group(1), ""))

    return VARIABLE_RE.sub(replace, text or "")


def contact_variables(contact, company=None) -> dict[str, str]:
    return {
        "first_name": contact.first_name or "there",
        "last_name": contact.last_name or "",
        "email": contact.email,
        "job_title": contact.job_title or "",
        "website": contact.website or "",
        "industry": contact.industry or "",
        "company_name": (company.name if company else "") or "your company",
    }
