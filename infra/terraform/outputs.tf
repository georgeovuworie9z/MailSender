output "send_email_function_name" {
  description = "Name of the send Lambda (use with `aws lambda invoke`)."
  value       = aws_lambda_function.send_email.function_name
}

output "send_email_function_arn" {
  value = aws_lambda_function.send_email.arn
}

output "send_email_log_group" {
  value = aws_cloudwatch_log_group.send_email.name
}

output "sender_identity_arn" {
  value = aws_sesv2_email_identity.sender.arn
}
