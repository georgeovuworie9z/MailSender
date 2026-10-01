import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

from mailsender import handler
from mailsender.logging_utils import JsonFormatter
from mailsender.mailer import Mailer, SendError

CONTEXT = SimpleNamespace(aws_request_id="req-1")


def test_success_returns_message_id(ses, valid_event):
    result = handler.lambda_handler(valid_event, CONTEXT)

    assert result["statusCode"] == 200
    assert result["messageId"]


def test_invalid_event_returns_400_without_calling_ses(monkeypatch):
    mailer = MagicMock()
    monkeypatch.setattr(handler, "_mailer", mailer)

    result = handler.lambda_handler({"to": "bad"}, CONTEXT)

    assert result["statusCode"] == 400
    assert "invalid email address" in result["error"]
    mailer.send.assert_not_called()


def test_permanent_ses_failure_returns_502(ses, valid_event, monkeypatch):
    monkeypatch.setenv("SENDER_EMAIL", "unverified@example.com")

    result = handler.lambda_handler(valid_event, CONTEXT)

    assert result["statusCode"] == 502
    assert result["error"] == "MessageRejected"


def test_retryable_ses_failure_is_raised(valid_event, monkeypatch):
    client = MagicMock()
    client.send_email.side_effect = ClientError(
        {"Error": {"Code": "TooManyRequestsException", "Message": "slow down"}}, "SendEmail"
    )
    monkeypatch.setattr(handler, "_mailer", Mailer("sender@example.com", client=client))

    with pytest.raises(SendError):
        handler.lambda_handler(valid_event, CONTEXT)


def test_logs_are_json(ses, valid_event, monkeypatch):
    records = []
    monkeypatch.setattr(handler.logger, "handle", records.append)

    handler.lambda_handler(valid_event, CONTEXT)

    log = json.loads(JsonFormatter().format(records[-1]))
    assert log["message"] == "email sent"
    assert log["request_id"] == "req-1"
    assert log["message_id"]
