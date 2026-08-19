from app.utils.column_mapping import normalize_contact_row, pick_email, pick_phone

DECISION_MAKER_ROW = {
    "emails": "magued.rayes@moneris.com;magued.personal@gmail.com",
    "countries": "canada;egypt",
    "first_name": "magued",
    "full_name": "magued rayes",
    "gender": "male",
    "industry": "financial services",
    "job_company_name": "moneris",
    "job_company_size": "1001-5000",
    "job_company_website": "moneris.com",
    "job_title": "vice president",
    "linkedin_connections": "2.0",
    "linkedin_url": "linkedin.com/in/magued-rayes-73a6a624",
    "linkedin_username": "magued-rayes-73a6a624",
    "location_country": "canada",
    "mobile_phone": "447922834305.0",
    "phone_numbers": "+14167204678",
    "skills": "finance;portfolio management;mergers and acquisitions",
    "work_email": "magued.rayes@moneris.com",
}


def test_full_decision_makers_row():
    row = normalize_contact_row(DECISION_MAKER_ROW)
    assert row["email"] == "magued.rayes@moneris.com"
    assert row["first_name"] == "Magued"
    assert row["last_name"] == "Rayes"
    assert row["full_name"] == "Magued Rayes"
    assert row["company"] == "Moneris"
    assert row["company_size"] == "1001-5000"
    assert row["job_title"] == "Vice President"
    assert row["industry"] == "Financial Services"
    assert row["country"] == "Canada"
    assert row["linkedin"] == "https://linkedin.com/in/magued-rayes-73a6a624"
    assert row["phone"] == "+447922834305"  # float artifact stripped, + prefixed
    assert row["skills"].startswith("finance;portfolio management")
    assert row["website"] == "moneris.com"
    assert row["gender"] == "male"


def test_work_email_preferred_over_emails_list():
    assert pick_email({"work_email": "a@corp.com", "emails": "b@gmail.com"}) == "a@corp.com"


def test_falls_back_to_first_valid_in_emails_list():
    assert pick_email({"work_email": "", "emails": "not-valid;b@gmail.com"}) == "b@gmail.com"


def test_missing_work_email_uses_emails():
    # 43.6% of Decision_Makers rows have no work_email
    assert pick_email({"emails": "x@y.co"}) == "x@y.co"


def test_generic_layout_still_works():
    row = normalize_contact_row(
        {"first_name": "Sarah", "last_name": "Chen", "email": "sarah@abc.ai",
         "company": "ABC AI", "job_title": "CTO", "industry": "AI"}
    )
    assert row["email"] == "sarah@abc.ai"
    assert row["company"] == "ABC AI"
    assert row["full_name"] == "Sarah Chen"


def test_last_name_derived_from_full_name():
    row = normalize_contact_row({"first_name": "magued", "full_name": "magued el rayes", "emails": "m@x.co"})
    assert row["last_name"] == "El Rayes"


def test_phone_fallback_to_phone_numbers():
    assert pick_phone({"mobile_phone": "", "phone_numbers": "+14167204678;+14160000000"}) == "+14167204678"


def test_no_email_row_is_invalid():
    row = normalize_contact_row({"first_name": "x", "full_name": "x y"})
    assert row["email"] == ""
