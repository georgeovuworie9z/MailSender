"""Send request model and validation.

Kept free of AWS code so it can be reused by any entry point
(direct invoke, SQS consumer, scheduled campaign).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

MAX_RECIPIENTS = 50  # SES limit per message (To + Cc + Bcc)
MAX_SUBJECT_LENGTH = 998  # RFC 5322 line length limit

# Pragmatic check, not full RFC 5322: one @, no whitespace, a dot in the domain.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ValidationError(ValueError):
    """Raised when a send request is malformed."""


@dataclass(frozen=True)
class SendRequest:
    to: list[str]
    subject: str
    text: str | None = None
    html: str | None = None
    cc: list[str] | None = None
    bcc: list[str] | None = None
    reply_to: list[str] | None = None

    @classmethod
    def from_dict(cls, data: Any) -> SendRequest:
        if not isinstance(data, dict):
            raise ValidationError("request body must be a JSON object")

        to = _address_list(data.get("to"), "to", required=True)
        cc = _address_list(data.get("cc"), "cc")
        bcc = _address_list(data.get("bcc"), "bcc")
        reply_to = _address_list(data.get("reply_to"), "reply_to")

        total = len(to) + len(cc or []) + len(bcc or [])
        if total > MAX_RECIPIENTS:
            raise ValidationError(f"too many recipients ({total}); maximum is {MAX_RECIPIENTS}")

        subject = data.get("subject")
        if not isinstance(subject, str) or not subject.strip():
            raise ValidationError("'subject' is required and must be a non-empty string")
        if len(subject) > MAX_SUBJECT_LENGTH:
            raise ValidationError(f"'subject' exceeds {MAX_SUBJECT_LENGTH} characters")

        text = _optional_str(data.get("text"), "text")
        html = _optional_str(data.get("html"), "html")
        if not text and not html:
            raise ValidationError("at least one of 'text' or 'html' is required")

        return cls(
            to=to,
            subject=subject.strip(),
            text=text,
            html=html,
            cc=cc,
            bcc=bcc,
            reply_to=reply_to,
        )


def _address_list(value: Any, field: str, *, required: bool = False) -> list[str] | None:
    if value is None:
        if required:
            raise ValidationError(f"'{field}' is required")
        return None
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list) or not value:
        raise ValidationError(f"'{field}' must be an email address or a non-empty list of them")

    addresses = []
    for item in value:
        if not isinstance(item, str) or not _EMAIL_RE.match(item.strip()):
            raise ValidationError(f"invalid email address in '{field}': {item!r}")
        addresses.append(item.strip())
    return addresses


def _optional_str(value: Any, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValidationError(f"'{field}' must be a string")
    return value or None
