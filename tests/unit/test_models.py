import pytest

from mailsender.models import MAX_RECIPIENTS, SendRequest, ValidationError


def test_valid_request_parses(valid_event):
    req = SendRequest.from_dict(valid_event)
    assert req.to == ["recipient@example.com"]
    assert req.subject == "Hello"
    assert req.text == "Plain body"
    assert req.html == "<p>HTML body</p>"
    assert req.cc is None


def test_single_address_string_is_accepted():
    req = SendRequest.from_dict({"to": "a@example.com", "subject": "s", "text": "t"})
    assert req.to == ["a@example.com"]


def test_whitespace_is_trimmed():
    req = SendRequest.from_dict({"to": [" a@example.com "], "subject": "  s  ", "text": "t"})
    assert req.to == ["a@example.com"]
    assert req.subject == "s"


def test_html_only_is_allowed():
    req = SendRequest.from_dict({"to": "a@example.com", "subject": "s", "html": "<b>x</b>"})
    assert req.text is None
    assert req.html == "<b>x</b>"


@pytest.mark.parametrize(
    ("event", "message"),
    [
        ("not a dict", "JSON object"),
        ({"subject": "s", "text": "t"}, "'to' is required"),
        ({"to": [], "subject": "s", "text": "t"}, "non-empty list"),
        ({"to": "not-an-email", "subject": "s", "text": "t"}, "invalid email address in 'to'"),
        ({"to": ["a@example.com", 42], "subject": "s", "text": "t"}, "invalid email address"),
        ({"to": "a@example.com", "cc": "bad", "subject": "s", "text": "t"}, "in 'cc'"),
        ({"to": "a@example.com", "text": "t"}, "'subject' is required"),
        ({"to": "a@example.com", "subject": "   ", "text": "t"}, "'subject' is required"),
        ({"to": "a@example.com", "subject": "x" * 999, "text": "t"}, "exceeds"),
        ({"to": "a@example.com", "subject": "s"}, "at least one of 'text' or 'html'"),
        ({"to": "a@example.com", "subject": "s", "text": ""}, "at least one of 'text' or 'html'"),
        ({"to": "a@example.com", "subject": "s", "text": 5}, "'text' must be a string"),
    ],
)
def test_invalid_requests_are_rejected(event, message):
    with pytest.raises(ValidationError, match=message):
        SendRequest.from_dict(event)


def test_recipient_limit_counts_to_cc_and_bcc():
    half = MAX_RECIPIENTS // 2
    event = {
        "to": [f"to{i}@example.com" for i in range(half)],
        "cc": [f"cc{i}@example.com" for i in range(half)],
        "bcc": ["one-too-many@example.com"],
        "subject": "s",
        "text": "t",
    }
    with pytest.raises(ValidationError, match="too many recipients"):
        SendRequest.from_dict(event)
