"""Thin wrapper around the SES v2 SendEmail API. All boto3 usage lives here."""

from __future__ import annotations

from typing import Any

import boto3
from botocore.exceptions import ClientError

from mailsender.models import SendRequest

# SES errors worth retrying (once SQS is in front of the Lambda, these go back on the queue).
RETRYABLE_ERROR_CODES = frozenset(
    {"TooManyRequestsException", "LimitExceededException", "Throttling", "ServiceUnavailable"}
)


class SendError(Exception):
    """SES rejected or failed to send a message."""

    def __init__(self, code: str, message: str, *, retryable: bool) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.retryable = retryable


class Mailer:
    def __init__(
        self,
        sender: str,
        *,
        configuration_set: str | None = None,
        client: Any = None,
    ) -> None:
        self.sender = sender
        self.configuration_set = configuration_set
        self._client = client or boto3.client("sesv2")

    def send(self, request: SendRequest) -> str:
        """Send one email and return the SES MessageId."""
        destination: dict[str, list[str]] = {"ToAddresses": request.to}
        if request.cc:
            destination["CcAddresses"] = request.cc
        if request.bcc:
            destination["BccAddresses"] = request.bcc

        body: dict[str, dict[str, str]] = {}
        if request.text:
            body["Text"] = {"Data": request.text, "Charset": "UTF-8"}
        if request.html:
            body["Html"] = {"Data": request.html, "Charset": "UTF-8"}

        params: dict[str, Any] = {
            "FromEmailAddress": self.sender,
            "Destination": destination,
            "Content": {
                "Simple": {
                    "Subject": {"Data": request.subject, "Charset": "UTF-8"},
                    "Body": body,
                }
            },
        }
        if request.reply_to:
            params["ReplyToAddresses"] = request.reply_to
        if self.configuration_set:
            params["ConfigurationSetName"] = self.configuration_set

        try:
            response = self._client.send_email(**params)
        except ClientError as exc:
            error = exc.response.get("Error", {})
            code = error.get("Code", "Unknown")
            raise SendError(
                code,
                error.get("Message", str(exc)),
                retryable=code in RETRYABLE_ERROR_CODES,
            ) from exc

        return response["MessageId"]
