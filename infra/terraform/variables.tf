variable "aws_region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "eu-north-1"
}

variable "project" {
  description = "Project name, used as a prefix for resource names."
  type        = string
  default     = "mailsender"
}

variable "environment" {
  description = "Deployment environment (e.g. dev, prod)."
  type        = string
  default     = "dev"
}

variable "sender_email" {
  description = "Email address mail is sent from. SES sends a verification link to it on first apply."
  type        = string

  validation {
    condition     = can(regex("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", var.sender_email))
    error_message = "sender_email must be a valid email address."
  }
}

variable "sandbox_recipient_emails" {
  description = <<-EOT
    Extra addresses to verify as recipients while the SES account is in sandbox mode.
    In the sandbox, SES only delivers to verified identities and checks IAM permissions
    against each recipient identity too. Leave empty once production access is granted.
  EOT
  type        = list(string)
  default     = []
}

variable "log_retention_days" {
  description = "CloudWatch log retention for Lambda functions."
  type        = number
  default     = 14
}

variable "lambda_log_level" {
  description = "Log level for the send Lambda."
  type        = string
  default     = "INFO"
}
