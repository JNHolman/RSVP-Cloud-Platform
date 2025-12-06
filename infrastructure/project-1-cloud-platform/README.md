RSVP Cloud Platform – Project 1

Highly available, cost-optimized AWS infrastructure for a scalable event-booking application.

Live Service URL: 👉 (http://rsvp-dev-alb-598230497.us-east-1.elb.amazonaws.com/)

📌 Business Problem

Event-driven businesses need:

High availability during peak RSVPs

Secure storage for customer data

Ability to scale automatically

Operational visibility

Fast detection + diagnosis of system issues

But small teams usually lack:

Cloud architecture expertise

Automated incident response

Standardized infrastructure

Efficient monitoring and alerting

The RSVP Cloud Platform solves this by delivering a production-grade AWS foundation using Terraform.

🎯 Business Solution

This platform provides:

⭐ High Availability

Multi-AZ architecture

Load balancing across multiple EC2 instances

Automatic scaling based on demand

⭐ Security by Design

Private subnets for compute + database

No publicly exposed EC2

Strict security groups

NAT + IGW architecture

⭐ Cost Efficiency

Small instance sizes

Autoscaling

Serverless AI features instead of expensive monitoring tools

⭐ AI-Powered Incident Response

When errors or CPU spikes occur:

A CloudWatch Alarm triggers

Lambda pulls logs → sends them to OpenAI

AI summarizes root cause

Summary stored in S3 + DynamoDB

SNS email sends human-readable diagnosis

🏗 Architecture Overview
Networking

VPC (10.0.0.0/16)

Public subnets (ALB)

Private subnets (EC2 + RDS)

Internet Gateway + NAT Gateway

Route tables for segmented traffic flow

Compute Layer

Auto Scaling Group (2–4 instances)

Apache web server installed via user_data

Private EC2 instances (not public)

Load Balancing

Application Load Balancer (ALB)

Health checks at /

ALB → Target Group → ASG

Database

Amazon RDS MySQL

Private-only access

SG allows inbound ONLY from EC2

Dev-sized DB for cost savings

Monitoring & Alerts

CloudWatch alarms for:

ALB 5xx spikes

High CPU on ASG

SNS notifications with summary

AI Operations Layer

Lambda triggered by EventBridge

Analyzes CloudWatch logs

Uses OpenAI for log summarization

Outputs stored in:

S3 (full summaries)

DynamoDB (metadata)

Emails the analysis to the engineer

🧩 Technology Stack
Layer	Technology
IaC	Terraform
Compute	EC2 (ASG)
Networking	VPC, Subnets, IGW, NAT
Load Balancer	ALB
Database	RDS MySQL
Monitoring	CloudWatch + SNS
Serverless	Lambda + EventBridge
AI	OpenAI GPT
Storage	S3 + DynamoDB
🚦 Deployment
terraform init
terraform plan
terraform apply


Terraform outputs include:

ALB DNS

RDS endpoint

S3 bucket name

DynamoDB table

SNS ARN

📸 Demo UI (Rendered Automatically on EC2)

The platform includes a custom HTML system dashboard showing:

Environment details

Network architecture

Compute details

AI layer status

Instance identity

(Add screenshot here after uploading to GitHub.)

🔮 Future Enhancements
1. HTTPS/TLS

ACM certificate

ALB 443 listener

Redirect HTTP → HTTPS

2. Secrets Management

Move DB passwords + OpenAI keys into:

SSM Parameter Store

or Secrets Manager

3. Application Logging

CloudWatch agent on EC2

ALB access logs → S3

4. Scaling Policies

CPU or RequestCount-based autoscaling

5. RDS Hardening

Backup retention

Multi-AZ failover

Deletion protection

6. Secure Admin Access

SSM Session Manager

or Bastion host

7. Terraform CI/CD

Validate

fmt

lint

plan on PRs

💼 Business Value Summary

This project demonstrates:

Real-world AWS architecture

Production-ready networking and security

Automated incident response using AI

Clean, modular Terraform IaC

Platform engineering best practices

It forms the foundation for a scalable cloud application supporting RSVP Society’s event operations.
