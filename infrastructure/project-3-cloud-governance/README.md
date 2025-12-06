RSVP Enterprise Cloud Governance – Project 3

Multi-account AWS foundation with centralized security, monitoring, compliance, and AI-assisted incident response.
Built for real organizations adopting cloud at scale.

Live Service URL: 👉 http://rsvp-cloud-governance-dashboard.s3-website-us-east-1.amazonaws.com/

📌 Business Problem

As organizations expand into the cloud, they face challenges:

No clear separation between environments (dev, staging, prod)

Security misconfigurations across accounts

Lack of centralized logging or guardrails

No oversight on spending

Manual incident response slows down recovery

Difficulty meeting compliance requirements

Without governance, businesses risk:

Security breaches

High costs

Operational failures

Compliance violations

🎯 Business Solution

Project 3 introduces an enterprise-grade multi-account AWS structure, delivering:

⭐ Multi-Account Architecture

AWS Organizations

Separate accounts for:

Security

Logging

Development

Production

⭐ Security Guardrails

Service Control Policies (SCPs)

Prevent risky actions:

No public S3

No deleting CloudTrail

No disabling GuardDuty

No unencrypted EBS volumes

⭐ Centralized Logging

Organization-wide CloudTrail

All logs flow into centralized Logging Account

S3 buckets with lifecycle management

⭐ Unified Identity

AWS IAM Identity Center (SSO)

Federated access with user permissions boundaries

⭐ Cost Governance

AWS Budgets

Alerts for spending thresholds

Tag policies for proper cost allocation

⭐ AI Incident Assistant

When GuardDuty, Config, or CloudWatch detect issues:

EventBridge triggers AI Lambda

Lambda fetches logs (CloudTrail, VPC Flow Logs, GuardDuty findings)

OpenAI summarizes:

What happened

Which resources were impacted

Likely root cause

Recommended remediation

Summary stored in DynamoDB and S3

Email or Slack notification goes to engineering

This replaces hours of manual log triage with instant insights.

🏗 Architecture Overview
1. AWS Organizations

Root → OU structure:

Security OU

Workloads OU

Sandbox OU

2. Security Baselines

SCPs for compliance

Restriction policies

Allowed regions

Mandatory encryption

3. Centralized Monitoring

GuardDuty enabled across all accounts

Config rules organization-wide

CloudTrail aggregated to Logging Account

4. AI Incident Response Pipeline

EventBridge rules capture:

Config non-compliance

GuardDuty findings

Budget alarms

CloudWatch anomalies

Lambda → OpenAI → Slack/SNS

5. Cost Guardrails

Monthly + daily budgets

Spend anomaly alerts

Tag enforcement

🧩 Technology Stack
Layer	Technology
Governance	AWS Organizations, SCPs
Identity	IAM Identity Center
Security	GuardDuty, Config, IAM
Logging	CloudTrail, S3, CloudWatch
Monitoring	EventBridge, SNS
AI	OpenAI GPT
Storage	DynamoDB + S3
Automation	Terraform
🚦 Deployment
terraform init
terraform apply


This project deploys organization-wide resources (multi-account).

🔮 Future Enhancements
1. Automated Compliance Reports

Weekly reports emailed to leadership

Summarized by AI

2. Real-Time Slack Bot

A chatbot that answers:

“Why did GuardDuty trigger this alert?”
Live, using OpenAI.

3. Drift Detection

Automatic drift scanning

Auto-fix of certain violations

4. Cross-Account Data Plane Controls

Centralized VPC ingress/egress management

💼 Business Value Summary

This project demonstrates your ability to design enterprise cloud foundations:

Secure, scalable multi-account architecture

Compliance-ready security baselines

Unified governance framework

AI-powered operational intelligence

Multi-team cloud enablement

It shows mastery of real cloud architecture used in mid-size and enterprise companies.
