# The function has no third-party dependencies (boto3 ships with the runtime),
# so the package is just the source tree zipped.
data "archive_file" "send_email" {
  type        = "zip"
  source_dir  = "${path.module}/../../src"
  output_path = "${path.module}/../../build/send_email.zip"
  excludes    = ["**/__pycache__/**"]
}

# Created explicitly so retention is set and Terraform owns (and destroys) it.
resource "aws_cloudwatch_log_group" "send_email" {
  name              = "/aws/lambda/${local.name_prefix}-send-email"
  retention_in_days = var.log_retention_days
}

resource "aws_lambda_function" "send_email" {
  function_name    = "${local.name_prefix}-send-email"
  description      = "Validates a send request and delivers it through SES."
  role             = aws_iam_role.send_email.arn
  runtime          = "python3.13"
  architectures    = ["arm64"]
  handler          = "mailsender.handler.lambda_handler"
  filename         = data.archive_file.send_email.output_path
  source_code_hash = data.archive_file.send_email.output_base64sha256
  memory_size      = 128
  timeout          = 10

  environment {
    variables = {
      SENDER_EMAIL = var.sender_email
      LOG_LEVEL    = var.lambda_log_level
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.send_email,
    aws_iam_role_policy.send_email,
  ]
}
