# MailSender

Serverless, event-driven email platform in Python on AWS, built as a portfolio project for a Cloud Solutions Architect CV.
Everything described on the CV should be real in this repo, so build each service listed below.

## Target architecture
- **API Gateway** – HTTPS endpoint that accepts send requests
- **SQS** (+ dead-letter queue) – buffers requests, retries failures
- **Lambda (Python)** – consumes the queue and sends mail
- **SES** – email delivery
- **EventBridge** – scheduled / recurring campaigns
- **SNS** – SES bounce and complaint notifications
- **DynamoDB** – templates and delivery status
- **IAM** – least-privilege role per function
- **CloudWatch** – logs, metrics, alarms

Infrastructure as Code: **Terraform**. Region: **eu-north-1 (Stockholm)** unless the user says otherwise.

## Build phases
1. Core send path: Lambda + SES, Terraform scaffold, unit tests
2. API Gateway + SQS (with DLQ)
3. DynamoDB (templates, status) + SNS bounce/complaint handling
4. EventBridge scheduling, CloudWatch alarms, IAM tightening
5. README with architecture diagram, GitHub Actions CI (lint, tests, terraform validate)

## Status / open items
- AWS CLI is installed but **not signed in yet**; the user must run `aws login` or `aws configure` themselves (never enter credentials for them).
- Need the user's **verified SES sender email** before deploying.
- New SES accounts are in sandbox mode: can only send to verified addresses until production access is requested.
- Keep costs within or near the AWS Free Tier.
