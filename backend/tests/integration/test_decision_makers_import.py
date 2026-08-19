"""Import an actual Decision_Makers-style .xlsx through the API."""
import io

from openpyxl import Workbook

COLUMNS = [
    "emails", "countries", "first_name", "full_name", "gender", "industry",
    "job_company_name", "job_company_size", "job_company_website", "job_title",
    "linkedin_connections", "linkedin_url", "linkedin_username",
    "location_country", "mobile_phone", "phone_numbers", "skills", "work_email",
]

ROWS = [
    # full row — work_email present
    ["magued.rayes@moneris.com;magued@gmail.com", "canada", "magued", "magued rayes",
     "male", "financial services", "moneris", "1001-5000", "moneris.com",
     "vice president", 2.0, "linkedin.com/in/magued-rayes-73a6a624",
     "magued-rayes-73a6a624", "canada", 447922834305.0, "+14167204678",
     "finance;portfolio management", "magued.rayes@moneris.com"],
    # no work_email — falls back to emails list
    ["sarah.chen@cibc.com", "canada", "sarah", "sarah chen", "female", "banking",
     "cibc", "10001+", "cibc.com", "director", 350.0,
     "linkedin.com/in/sarah-chen-1", "sarah-chen-1", "canada", None, None,
     "risk management;leadership", None],
    # no valid email anywhere → invalid
    [None, "canada", "john", "john doe", "male", "banking", "rbc", "10001+",
     "rbc.com", "partner", 120.0, "linkedin.com/in/john-doe-9", "john-doe-9",
     "canada", None, None, None, None],
    # duplicate of row 1
    ["magued.rayes@moneris.com", "canada", "magued", "magued rayes", "male",
     "financial services", "moneris", "1001-5000", "moneris.com",
     "vice president", 2.0, "linkedin.com/in/magued-rayes-73a6a624",
     "magued-rayes-73a6a624", "canada", None, None, None,
     "magued.rayes@moneris.com"],
]


def _xlsx_bytes() -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.append(COLUMNS)
    for row in ROWS:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_decision_makers_xlsx_import(client, auth_headers):
    content = _xlsx_bytes()

    r = client.post(
        "/api/imports/preview",
        files={"file": ("Decision_Makers.xlsx", content,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 4
    assert data["valid"] == 2
    assert data["invalid"] == 1
    assert data["duplicates"] == 1
    # preview rows are already normalized
    assert data["sample_rows"][0]["full_name"] == "Magued Rayes"
    assert data["sample_rows"][0]["phone"] == "+447922834305"

    r = client.post(
        "/api/imports/run",
        files={"file": ("Decision_Makers.xlsx", content,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=auth_headers,
    )
    assert r.json()["imported"] == 2

    r = client.get("/api/contacts?search=magued", headers=auth_headers)
    items = r.json()["items"]
    assert len(items) == 1
    c = items[0]
    assert c["email"] == "magued.rayes@moneris.com"     # work_email won
    assert c["full_name"] == "Magued Rayes"
    assert c["job_title"] == "Vice President"
    assert c["company_size"] == "1001-5000"
    assert c["country"] == "Canada"
    assert c["linkedin"].startswith("https://linkedin.com/in/")
    assert c["skills"] == "finance;portfolio management"

    # filters work on the new columns
    r = client.get("/api/contacts?company_size=10001%2B", headers=auth_headers)
    assert r.json()["total"] == 1
    assert r.json()["items"][0]["first_name"] == "Sarah"

    r = client.get("/api/contacts?country=canada", headers=auth_headers)
    assert r.json()["total"] == 2
