# Creating an email identity makes SES send a verification link to the address.
# Sending works only after the link has been clicked.
resource "aws_sesv2_email_identity" "sender" {
  email_identity = var.sender_email
}

resource "aws_sesv2_email_identity" "sandbox_recipient" {
  for_each       = toset([for e in var.sandbox_recipient_emails : e if e != var.sender_email])
  email_identity = each.value
}

locals {
  # Identities the Lambda may send through or to (the sandbox checks recipients as well).
  ses_identity_arns = concat(
    [aws_sesv2_email_identity.sender.arn],
    [for id in aws_sesv2_email_identity.sandbox_recipient : id.arn],
  )
}
