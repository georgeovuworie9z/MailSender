from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError
from moto.core import DEFAULT_ACCOUNT_ID
from moto.ses.models import ses_backends

from mailsender.mailer import Mailer, SendError
from mailsender.models import SendRequest
from tests.conftest import SENDER


def _sent_messages():
    return ses_backends[DEFAULT_ACCOUNT_ID]["eu-north-1"].sent_messages


def test_send_returns_message_id_and_delivers(ses, valid_event):
    request = SendRequest.from_dict({**valid_event, "cc": ["cc@example.com"], "reply_to": "r@example.com"})

    message_id = Mailer(SENDER, client=ses).send(request)

    assert message_id
    sent = _sent_messages()
    assert len(sent) == 1
    assert sent[0].source == SENDER
    assert sent[0].destinations["ToAddresses"] == ["recipient@example.com"]
    assert sent[0].destinations["CcAddresses"] == ["cc@example.com"]


def test_unverified_sender_is_permanent_failure(ses, valid_event):
    mailer = Mailer("unverified@example.com", client=ses)

    with pytest.raises(SendError) as exc_info:
        mailer.send(SendRequest.from_dict(valid_event))

    assert exc_info.value.code == "MessageRejected"
    assert exc_info.value.retryable is False


def _client_raising(code):
    client = MagicMock()
    client.send_email.side_effect = ClientError({"Error": {"Code": code, "Message": "boom"}}, "SendEmail")
    return client


@pytest.mark.parametrize("code", ["TooManyRequestsException", "LimitExceededException", "Throttling"])
def test_throttling_is_retryable(code, valid_event):
    with pytest.raises(SendError) as exc_info:
        Mailer(SENDER, client=_client_raising(code)).send(SendRequest.from_dict(valid_event))
    assert exc_info.value.retryable is True


def test_request_shape_sent_to_ses(valid_event):
    client = MagicMock()
    client.send_email.return_value = {"MessageId": "abc-123"}
    mailer = Mailer(SENDER, configuration_set="mailsender-dev", client=client)

    assert mailer.send(SendRequest.from_dict({**valid_event, "html": None})) == "abc-123"

    params = client.send_email.call_args.kwargs
    assert params["FromEmailAddress"] == SENDER
    assert params["ConfigurationSetName"] == "mailsender-dev"
    body = params["Content"]["Simple"]["Body"]
    assert body == {"Text": {"Data": "Plain body", "Charset": "UTF-8"}}
    assert "CcAddresses" not in params["Destination"]
    assert "ReplyToAddresses" not in params
