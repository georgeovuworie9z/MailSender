data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "send_email" {
  name               = "${local.name_prefix}-send-email"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

# Least privilege: send only from the configured sender identity, and write
# logs only to this function's own log group.
data "aws_iam_policy_document" "send_email" {
  statement {
    sid       = "SendFromVerifiedSender"
    actions   = ["ses:SendEmail"]
    resources = local.ses_identity_arns

    condition {
      test     = "StringEquals"
      variable = "ses:FromAddress"
      values   = [var.sender_email]
    }
  }

  statement {
    sid       = "WriteOwnLogs"
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["${aws_cloudwatch_log_group.send_email.arn}:*"]
  }
}

resource "aws_iam_role_policy" "send_email" {
  name   = "send-email"
  role   = aws_iam_role.send_email.id
  policy = data.aws_iam_policy_document.send_email.json
}
