import boto3
import pytest
from moto import mock_aws

from mailsender import handler

SENDER = "sender@example.com"


@pytest.fixture(autouse=True)
def aws_env(monkeypatch):
    """Fake credentials so nothing can ever reach a real AWS account."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "eu-north-1")
    monkeypatch.setenv("SENDER_EMAIL", SENDER)
    monkeypatch.delenv("CONFIGURATION_SET", raising=False)
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    # Drop the cached client so each test gets one bound to its own mock.
    monkeypatch.setattr(handler, "_mailer", None)


@pytest.fixture
def ses():
    with mock_aws():
        client = boto3.client("sesv2", region_name="eu-north-1")
        client.create_email_identity(EmailIdentity=SENDER)
        yield client


@pytest.fixture
def valid_event():
    return {
        "to": ["recipient@example.com"],
        "subject": "Hello",
        "text": "Plain body",
        "html": "<p>HTML body</p>",
    }
