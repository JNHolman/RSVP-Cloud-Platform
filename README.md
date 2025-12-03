RSVP Cloud Platform
Highly available, cost-optimized, AI-powered AWS infrastructure — deployed fully with Terraform.
<div align="center"> <img src="screenshots/ui.png" width="80%" style="border-radius:12px;" /> </div>
Project Overview

The RSVP Cloud Platform is a complete AWS environment designed for a small event-booking application.
It demonstrates professional-grade cloud engineering skills across:

<<<<<<< HEAD
A highly available, cost-optimized AWS infrastructure for a small event-booking platform. Includes VPC, EC2, ALB, RDS, IAM hardening, monitoring, and AI-powered log summarization for operational insight.

Business Problem

A small event-booking platform needs to run reliably at low cost.
They need:

A secure public web app
A backend database
Centralized logging and monitoring
Automated insights into failures
Infrastructure that’s simple to maintain
Deployment that avoids human error

The goal: build a production-ready, budget-friendly cloud platform that solves an actual business need — not just “use AWS services.”

Architecture Overview
                       ┌───────────────────────────┐
                       │        AWS Users          │
                       └──────────────┬────────────┘
                                      │
                                HTTPS (ALB)
                                      │
                      ┌───────────────▼────────────────┐
                      │      Application Load Balancer  │
                      └───────────────┬────────────────┘
                                      │
                         Private Subnets (Multi-AZ)
                                      │
           ┌──────────────────────────┴────────────────────────┐
           │                                                  │
┌──────────▼─────────┐                             ┌──────────▼─────────┐
│    EC2 Web App     │   → App Logs → CloudWatch   │  RDS (PostgreSQL)  │
│   (Auto Recovery)  │   → AI Summaries (Bedrock)  │   Multi-AZ Backup   │
└──────────▲─────────┘                             └──────────▲─────────┘
           │                                                  │
           └──────────────┬──────────────────────────────────┘
                          │
                 ┌────────▼────────┐
                 │   IAM Secure    │
                 │  Least Privilege│
                 └──────────────────┘

Key Features

1. Multi-AZ VPC Design
Public + private subnets
NAT gateway for outgoing traffic
Security groups & NACLs

Why?
Balanced reliability vs. cost. Single NAT instead of multi-NAT to save $30–$60/month.

2. EC2 Web Tier (Auto-Recovery)
EC2 instance hosting the RSVP application
Auto Recovery enabled
ALB for load balancing + health checks

Why EC2 over Fargate?
Lower monthly cost for low-traffic applications.

3. RDS PostgreSQL (Multi-AZ)
Automated backups
Encryption at rest
Parameter group hardening

Why not DynamoDB?
RDS is better for transactional app data and relational queries.

4. IAM Hardening
Role-based access
MFA for admin
CloudTrail + GuardDuty

Why?
Cloud security is a first-class requirement: not a “nice to have.”

5. Monitoring & Observability
CloudWatch dashboards
CloudWatch alarms
RDS enhanced monitoring

6. AI-Powered Log Summarization

CloudWatch Logs → Lambda → Amazon Bedrock (Llama3 / Claude Haiku) → daily summaries.

This solves a REAL business problem:
Faster troubleshooting
Non-technical business owners get “plain-English” insights
Reduces MTTR and improves transparency

Infrastructure as Code (Terraform)
All infrastructure is codified using Terraform:
VPC + subnets
EC2 instance
ALB + target group + listener
RDS instance
IAM roles & policies
CloudWatch alarms
S3 logging bucket

Why Terraform?
Repeatability
Version-controlled infrastructure
Eliminates human error
Matches modern Cloud/DevOps hiring expectations

CI/CD Pipeline (GitHub Actions)

Pipeline includes:
Terraform fmt / validate
Terraform plan
Terraform apply (manual approval)
Version tagging

Why GitHub Actions?
Native integration with GitHub and free for personal projects.

Cost Model (Monthly Estimate)
Component	Cost
EC2 t3.micro	~$8
ALB	~$18
RDS t3.micro Multi-AZ	~$50
NAT Gateway	~$32
S3 Logs	~$1
CloudWatch	~$3
Total	~$112/month

This proves budget awareness, which is critical in cloud hiring.

Tradeoffs & Decisions
Reliability vs. Cost

1 NAT gateway instead of 2
EC2 instead of Fargate
Multi-AZ RDS (more cost, but needed for uptime)
Speed vs. Security
Public ALB, private EC2
IAM least-privilege
Mandatory logging & monitoring

Simplicity vs. Future Growth
Terraform modules
Easy to scale to autoscaling group
App can later move to Fargate or Lambda

What I Would Improve Next

Add autoscaling group for EC2
Add WAF for ALB
Convert logs to OpenTelemetry format
Introduce S3 static content + CloudFront
Expand Bedrock AI to detect anomalous logs
=======
✔ Infrastructure as Code (Terraform)
✔ VPC design (public + private subnets)
✔ Compute (EC2 in private subnets)
✔ Load balancing (ALB)
✔ Database layer (RDS MySQL)
✔ Observability (CloudWatch alarms + dashboard)
✔ AI-powered log summarization (Lambda + DynamoDB + S3 + OpenAI API)

This is a production-style architecture, built end-to-end by Josh Holman.

Architecture Diagram
<div align="center"> <img src="screenshots/architecture.png" width="85%" /> </div>
🏗 Full AWS Architecture
Core Infra
Layer	Service	Description
Network	VPC, IGW, NAT, Route Tables	10.0.0.0/16 VPC with public + private subnets
Compute	EC2 Auto-scaled pair	App servers in private subnets
Load Balancer	ALB	Handles all incoming HTTP traffic
Database	RDS MySQL	Single-AZ dev DB
AI/Serverless	Lambda, DynamoDB, S3	OpenAI-backed log summarization
Monitoring	CloudWatch alarms + dashboard	ALB 5xx, EC2 CPU
⚡ Tech Stack & Tools
<div align="center">


















</div>
Repository Structure
RSVP-Cloud-Platform/
│── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── vpc.tf
│   ├── ec2.tf
│   ├── alb.tf
│   ├── rds.tf
│   ├── monitoring.tf
│   ├── ai-logs.tf
│   ├── lambda_function.py
│   ├── ai_lambda_package.zip
│   └── terraform.tfvars
│
│── screenshots/
│   ├── ui.png
│   ├── vpc.png
│   ├── ec2.png
│   ├── alb.png
│   ├── rds.png
│   ├── cloudwatch.png
│   ├── lambda.png
│   ├── s3.png
│   ├── dynamodb.png
│   └── terraform-output.png
│
│── README.md
│── LICENSE
│── .gitignore

Screenshots
🌐 Application UI
<img src="screenshots/ui.png" width="80%" />
🛜 VPC Layout
<img src="screenshots/vpc.png" width="80%" />
⚖️ Application Load Balancer
<img src="screenshots/alb.png" width="80%" />
💻 EC2 Instances
<img src="screenshots/ec2.png" width="80%" />
🗄 RDS MySQL
<img src="screenshots/rds.png" width="80%" />
📊 CloudWatch Monitoring
<img src="screenshots/cloudwatch.png" width="80%" />
🤖 AI Log Summarizer Lambda
<img src="screenshots/lambda.png" width="80%" />
📦 S3 Log Storage
<img src="screenshots/s3.png" width="80%" />
🧩 DynamoDB Log History
<img src="screenshots/dynamodb.png" width="80%" />
🧠 AI Log Summarization Pipeline

The project includes a complete AI pipeline:

CloudWatch logs → Lambda

Lambda uses the OpenAI API to generate summaries

Summary is stored in S3

Metadata saved in DynamoDB

Terraform provisions all pieces automatically

Example output:

{
  "status": "ok",
  "summary_saved": "summary-2025-12-02T22:11:11.766946.txt",
  "preview": "Service healthy. No anomalies detected."
}

Deployment Steps
1. Initialize Terraform
terraform init

2. Validate
terraform validate

3. Apply
terraform apply

4. Get outputs
terraform output

🧹 Destroy Infra
terraform destroy

Author

Josh Holman
Cloud & Network Engineer
Louisville, KY
>>>>>>> Updated README and synced Terraform files
