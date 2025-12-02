RSVP Cloud Platform

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
