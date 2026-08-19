import pytest

from app.utils.excel_parser import parse_contact_file


def test_parses_csv():
    content = b"first_name,last_name,email,company\nSarah,Chen,sarah@abc.ai,ABC AI\n"
    rows = parse_contact_file("contacts.csv", content)
    assert rows == [
        {"first_name": "Sarah", "last_name": "Chen", "email": "sarah@abc.ai", "company": "ABC AI"}
    ]


def test_normalizes_headers():
    content = b"First Name,EMAIL\nJo,jo@x.io\n"
    rows = parse_contact_file("contacts.csv", content)
    assert rows[0]["first_name"] == "Jo"
    assert rows[0]["email"] == "jo@x.io"


def test_rejects_unknown_extension():
    with pytest.raises(ValueError):
        parse_contact_file("contacts.txt", b"hello")


def test_rejects_huge_files():
    with pytest.raises(ValueError):
        parse_contact_file("contacts.csv", b"x" * (11 * 1024 * 1024))
