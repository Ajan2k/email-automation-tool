from app.email.renderer import render


def test_substitutes_variables():
    result = render("Hi {{first_name}} from {{company_name}}", {"first_name": "Sarah", "company_name": "ABC AI"})
    assert result == "Hi Sarah from ABC AI"


def test_missing_variable_becomes_empty():
    assert render("Hi {{unknown}}!", {}) == "Hi !"


def test_whitespace_tolerant():
    assert render("{{ first_name }}", {"first_name": "Jo"}) == "Jo"
