# Cloud Engineering Portfolio — RSVP Multi-Project AWS Platform

A three-project, production-style cloud platform showcasing modern AWS architecture, Infrastructure as Code, container orchestration, CI/CD automation, multi-account security, cost governance, and AI-assisted operations.

This portfolio demonstrates the full lifecycle of cloud engineering:

**Design → Deploy → Automate → Secure → Scale → Govern**

It reflects the type of work performed by Cloud Engineers, CloudOps Engineers, DevOps/Platform Engineers, and Cloud Security practitioners building and operating real systems.

---

## Business Context

**RSVP Society** is a modern events and nightlife brand that needs a cloud platform capable of supporting:

- Unpredictable event-driven traffic (ticket drops, RSVP spikes, promo campaigns)
- Fast updates to web and mobile features
- Strong security and cost visibility
- Reliability during peak demand
- Automated insight into logs, alerts, and incidents

This portfolio simulates what a Cloud Engineer would build for a startup or small business maturing toward enterprise-grade cloud operations.

---

## What This Portfolio Demonstrates

- Modern AWS architecture
- Infrastructure as Code (Terraform)
- Containerization and ECS orchestration
- CI/CD automation with GitHub Actions
- Multi-account security and governance
- Centralized logging and monitoring
- Cost control and automated budget alerts
- AI-driven log and incident summarization
- Practical CloudOps workflows
- Real-world business problem solving

---

## Project Index

| Project | Folder | Focus Area | Description |
|--------|--------|-----------|-------------|
| **Project 1 – RSVP Cloud Platform** | `infrastructure/project-1-cloud-platform` | Infrastructure Layer | VPC, ALB, EC2 Auto Scaling, RDS, CloudWatch, AI log summarization |
| **Project 2 – Container Platform & CI/CD** | `infrastructure/project-2-ecs-cicd` | Application Delivery Layer | Modernizes to Docker + ECS Fargate with GitHub Actions CI/CD |
| **Project 3 – Multi-Account Security & AI Incident Response** | `infrastructure/project-3-cloud-governance` | Enterprise Layer | Organizations, SCPs, Identity Center, GuardDuty, Security Hub, budgets, AI incident assistant |

Each project builds on the previous one, creating a unified platform from **infrastructure → application delivery → enterprise readiness**.

---

## Architecture Overview

The platform is structured as a three-layer cloud architecture:

1. **Infrastructure Layer (Project 1)**  
   - Multi-AZ VPC (public + private subnets)  
   - Application Load Balancer  
   - EC2 Auto Scaling Group  
   - RDS MySQL in private subnets  
   - NAT + IGW + custom route tables  
   - CloudWatch metrics and alarms → SNS  
   - AI Ops pipeline for log summarization (CloudWatch → SNS → Lambda → LLM → S3/DynamoDB)

2. **Application Delivery Layer (Project 2)**  
   - Dockerized web application  
   - Amazon ECR for image storage  
   - ECS Fargate service behind a load balancer  
   - GitHub Actions CI/CD pipeline (build → test → scan → push → deploy)  
   - Zero-downtime rolling deployments

3. **Enterprise Security & Operations Layer (Project 3)**  
   - AWS Organization with multiple accounts (Security, Dev, Prod)  
   - Service Control Policies (SCPs) for guardrails  
   - IAM Identity Center (SSO and permission sets)  
   - Centralized security services: GuardDuty, Security Hub, IAM Access Analyzer  
   - AWS Budgets and Cost Anomaly Detection  
   - AI Incident Assistant: GuardDuty/CloudWatch events → Lambda → LLM → human-readable incident summary

---

## How the Projects Work Together

**Layer** | **Project** | **What It Delivers** | **Why It Matters**
---|---|---|---
Infrastructure | Project 1 | VPC, compute, database, observability, AI log summaries | Reliable foundation for secure, scalable RSVP workloads
Application Delivery | Project 2 | Containers, ECS Fargate, CI/CD pipeline | Faster, safer deployments and modernized app delivery
Enterprise Security & Ops | Project 3 | Multi-account structure, guardrails, cost controls, AI incident analysis | Production-ready governance, compliance, and incident response

Together, these projects reflect what companies expect from a Cloud Engineer owning both **technical implementation** and **business impact**.

---

## Cost Optimization Strategy

The platform is designed to be realistic for a small-to-mid sized business:

- **Right-sized compute:** Auto Scaling EC2 and Fargate tasks scale with demand.
- **Private RDS:** Keeps data secure while avoiding unnecessary overhead.
- **IaC for environments:** Non-prod environments can be created/destroyed quickly.
- **Budgets + anomaly detection:** Owners get early warning on spend spikes.
- **Minimal NAT exposure:** Architected to avoid unnecessary data processing costs where possible.

Cost is treated as a **first-class design constraint**, not an afterthought.

---

## Future Enhancements

Planned improvements to evolve the RSVP platform:

1. **Serverless API & Event-Driven Workflows**
   - API Gateway + Lambda microservices
   - Step Functions for orchestration
   - EventBridge for decoupled workflows

2. **Infrastructure Testing & Policy as Code**
   - Terratest for infra validation
   - Checkov or OPA policies for security/compliance checks
   - Pre-commit hooks to block misconfigurations

3. **GitOps for Environment Management**
   - ArgoCD or Flux for declarative deployments
   - Git-driven promotion across dev → staging → prod
   - Drift detection between desired and actual state

4. **AI-Powered Cloud Operations Dashboard**
   - Central view for health, spend, alerts, and incidents
   - Natural language querying across logs, metrics, and incidents

---

## Contact

**Josh Holman**  
Cloud Engineer • Network Engineer • DevOps Practitioner  

https://www.linkedin.com/in/jnholmanjr/
jnholman@charter.net


