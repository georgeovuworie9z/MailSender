"""Lambda entry point for direct invocation.

Event shape:
    {"to": ["a@example.com"], "subject": "Hi", "text": "...", "html": "..."}

Returns {"statusCode": 200, "messageId": ...} on success, a 4xx/5xx result for
permanent failures, and raises on retryable SES errors so the caller (later SQS)
can retry.
"""

from __future__ import annotations

import os
from typing import Any

from mailsender.logging_utils import get_logger
from mailsender.mailer import Mailer, SendError
from mailsender.models import SendRequest, ValidationError

logger = get_logger(__name__)

_mailer: Mailer | None = None


def _get_mailer() -> Mailer:
    # Created on first use and reused across warm invocations.
    global _mailer
    if _mailer is None:
        _mailer = Mailer(
            sender=os.environ["SENDER_EMAIL"],
            configuration_set=os.environ.get("CONFIGURATION_SET") or None,
        )
    return _mailer


def lambda_handler(event: Any, context: Any) -> dict[str, Any]:
    request_id = getattr(context, "aws_request_id", None)

    try:
        request = SendRequest.from_dict(event)
    except ValidationError as exc:
        logger.warning("invalid request", extra={"fields": {"request_id": request_id, "error": str(exc)}})
        return {"statusCode": 400, "error": str(exc)}

    log_fields = {"request_id": request_id, "recipient_count": len(request.to)}

    try:
        message_id = _get_mailer().send(request)
    except SendError as exc:
        fields = {**log_fields, "error_code": exc.code, "retryable": exc.retryable}
        if exc.retryable:
            logger.warning("retryable send failure", extra={"fields": fields})
            raise
        logger.error("send rejected", extra={"fields": fields})
        return {"statusCode": 502, "error": exc.code, "message": exc.message}

    logger.info("email sent", extra={"fields": {**log_fields, "message_id": message_id}})
    return {"statusCode": 200, "messageId": message_id}
