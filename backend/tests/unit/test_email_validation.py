from app.utils.email_validation import is_valid_email, normalize_email


def test_valid_emails():
    assert is_valid_email("user@example.com")
    assert is_valid_email("first.last+tag@sub.domain.co")


def test_invalid_emails():
    assert not is_valid_email("")
    assert not is_valid_email("not-an-email")
    assert not is_valid_email("missing@tld")
    assert not is_valid_email("@example.com")


def test_normalize():
    assert normalize_email("  User@Example.COM ") == "user@example.com"
