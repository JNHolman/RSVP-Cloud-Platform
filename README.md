🌐 RSVP Cloud Platform — End-to-End Cloud Engineering Portfolio

A three-project portfolio demonstrating modern AWS architecture, security, automation, observability, and AI-assisted operations.

📌 Overview

The RSVP Cloud Platform is a complete, end-to-end cloud engineering portfolio designed to demonstrate real-world skills across:

Modern AWS architecture

Infrastructure as Code (Terraform)

Container orchestration and CI/CD

Multi-account security and governance

Cloud monitoring and automated incident workflows

AI-assisted operations using Lambda + OpenAI

This portfolio is structured across three production-quality projects, each building on the previous one, showcasing a full Cloud / DevOps engineering skill set, from foundational infrastructure all the way to enterprise-level governance and AI-powered incident response.

Together, these projects represent the full lifecycle of a cloud platform:

Design → Deploy → Automate → Secure → Scale → Govern

🧱 PROJECT BREAKDOWN
🚀 PROJECT 1 — RSVP Cloud Platform (Foundational Infrastructure Layer)
VPC • ALB • Auto Scaling • EC2 • RDS • CloudWatch • AI Log Summarization

Project 1 builds a highly available AWS environment designed for a small event-booking app. It includes:

Infrastructure

Multi-AZ VPC (public/private subnets)

Auto Scaling Group with EC2 app servers

Application Load Balancer (ALB)

RDS MySQL in private subnets

NAT Gateway, IGW, custom route tables

Security groups with least-privilege design

Observability

System metrics (CPU, RAM, status checks)

CloudWatch alarms routed to SNS

Dashboard for environment health

AI Operations Layer

CloudWatch → SNS → Lambda → AI log summarization

Automatic summaries stored in S3 and DynamoDB

Human-readable incident insights (what happened & why)

Business Problems Solved

✔ Creates a reliable, scalable backend foundation
✔ Ensures the application is always available
✔ Adds automated insight to logs (no manual digging)
✔ Reduces operational load with AI-driven summaries

This is what real companies expect from a Cloud Engineer handling an app migration or greenfield deployment.

📦 PROJECT 2 — Containerized Platform & CI/CD Pipeline (Developer Velocity Layer)
Docker • ECS Fargate • ECR • GitHub Actions • Immutable Deployments

Project 2 modernizes the application from EC2 → containers and introduces a full CI/CD pipeline.

Core Components

Containerized web app (Docker)

Automated builds pushed to Amazon ECR

ECS Fargate cluster for serverless containers

Load balanced service running across multiple AZs

GitHub Actions CI/CD pipeline:

Build → test → security scan → push → deploy

Zero-downtime rolling deployments

Business Problems Solved

✔ No more managing EC2 servers manually
✔ Faster deployments for developers
✔ Safer code releases with automated checks
✔ Lower infrastructure overhead and improved scaling

This layer represents what companies expect when upgrading legacy EC2 workloads toward a modern DevOps-friendly microservices architecture.

🛡 PROJECT 3 — Multi-Account Security, Cost Governance & AI-Incident Assistant (Enterprise Layer)
IAM Identity Center • SCPs • GuardDuty • Security Hub • Budgets • AI Incident Analysis

Project 3 elevates the platform to enterprise readiness.

Security & Governance

AWS Organization with multiple accounts (Security, Dev, Prod)

Service Control Policies (SCPs) for guardrails

IAM Identity Center for SSO + permission sets

Audit account for centralized logging

GuardDuty, Security Hub, IAM Access Analyzer enabled org-wide

Cost Optimization

AWS Budgets with automated alerts

Cost Anomaly Detection

Tagging enforcement policies

AI Incident Assistant

Detects GuardDuty or CloudWatch events

Lambda sends the event through an AI model

AI returns actionable summaries:
Root cause, impact, urgency, recommended remediation

Business Problems Solved

✔ Provides enterprise-grade security & compliance
✔ Centralizes monitoring and guardrails
✔ Prevents misconfigurations and account drift
✔ Reduces incident investigation time with AI insights

🔗 HOW ALL 3 PROJECTS WORK TOGETHER
Layer	Project	What It Delivers	Why It Matters
1. Infrastructure Layer	Project 1	VPC, EC2, ALB, RDS, CloudWatch, AI logs	The foundation for running secure, scalable applications
2. Application Delivery Layer	Project 2	Containers, ECS, CI/CD pipeline	Improves developer velocity, reduces ops overhead, modernizes architecture
3. Enterprise Security & Operations Layer	Project 3	Multi-account governance, budgets, guardrails, AI incident assistant	Makes the platform production-ready and compliant for a real company
Together, the platform demonstrates:

✔ Real-world cloud architecture
✔ Automated deployment workflows
✔ Enterprise security governance
✔ AI-augmented cloud operations
✔ Cost control and multi-account maturity

🏁 Future Enhancements

To continue evolving the RSVP Cloud Platform:

🔮 1. Project 4 — Serverless API & Event-Driven Architecture

API Gateway + Lambda microservices

Step Functions

EventBridge decoupled workflows

🔮 2. Add Infrastructure Testing

Terratest

Checkov or OPA policies

Pre-commit hooks

🔮 3. GitOps with ArgoCD or Flux

Full declarative Kubernetes or ECS config

Git-driven releases across environments

🔮 4. AI-Powered Dashboard

Centralized UI showing environment summaries, spending, alerts, incidents

LLM-powered natural language search for data across logs & metrics

📬 Contact
Josh Holman
Cloud Engineer • Network Engineer • DevOps Practitioner
