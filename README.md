# Cloud Engineering Portfolio — RSVP Multi-Project AWS Platform

A three-part AWS portfolio built with **Terraform** to show how I approach cloud infrastructure, application delivery, and governance/ops. It’s a **production-style lab**: deployable, verifiable, and designed to be torn down cleanly to control cost.

This repo is organized as:

**Build → Deploy → Operate**

---

## Business context (why this platform exists)

RSVP Society is an events/nightlife brand. A platform like this needs to handle:
- traffic spikes around promos and event drops
- frequent application updates
- clear visibility into outages and errors
- basic security hygiene and cost awareness

The goal here is not to claim “enterprise scale.” The goal is to show **real AWS patterns**, with **proof in Terraform, workflows, and screenshots**.

---

## What this portfolio demonstrates (implemented vs planned)

### Implemented in this repo
- **Terraform IaC** for AWS infrastructure
- **Multi-AZ networking patterns** (public/private subnets, routing)
- **EC2 + ALB + Auto Scaling + RDS** (Project 1)
- **ECS Fargate delivery** with **ECR** (Project 2)
- **GitHub Actions pipeline** that **builds and pushes** an image and **triggers an ECS redeploy** (Project 2)
- **Event-driven AI log summarization** (Project 1):  
  **CloudWatch Alarm State Change (EventBridge) → Lambda → OpenAI → S3 + DynamoDB → SNS**
- **Governance/security visibility** screenshots and baseline setup work (Project 3):  
  Organizations (enabled), IAM roles/policies, GuardDuty/Security Hub/CloudTrail/AWS Config pages

### Planned / partial (not counted as delivered yet)
- True **multi-account** structure (Security/Dev/Prod) with delegated admin + org-wide aggregation
- Full “AI incident response” workflow in Project 3 (Lambda + event routing + stored summaries)
- Tests/scans in CI/CD (Project 2) beyond build/push/redeploy

---

## Project index

| Project | Folder | Focus | What it does |
|---|---|---|---|
| Project 1 — RSVP Cloud Platform | [`infrastructure/project-1-cloud-platform`](./infrastructure/project-1-cloud-platform) | Infrastructure | VPC, ALB, EC2 Auto Scaling, RDS, CloudWatch alarms + **AI log summaries to S3/DynamoDB** |
| Project 2 — Container Platform & CI/CD | [`infrastructure/project-2-ecs-cicd`](./infrastructure/project-2-ecs-cicd) | Delivery | Docker + ECR + ECS Fargate behind an ALB + GitHub Actions build/push/redeploy |
| Project 3 — Governance & Security (Org / Ops Layer) | [`infrastructure/project-3-cloud-governance`](./infrastructure/project-3-cloud-governance) | Governance/Ops | Org/security tooling setup work + dashboard site; multi-account + AI incident workflow are planned |

Each project stands alone, but together they show a realistic progression from **infrastructure** → **delivery** → **governance/ops**.

---

## Architecture overview

![Platform Architecture Overview](platform-architecture-overview.png)

### Layer 1 — Infrastructure (Project 1)
Core components:
- VPC across 2+ AZs (public + private subnets)
- Internet Gateway + NAT (for private egress where needed)
- ALB + target groups
- EC2 Auto Scaling Group
- RDS MySQL (private subnets)
- CloudWatch alarms + SNS notifications
- **AI log summarization pipeline (implemented)**:
  - Trigger: **CloudWatch Alarm State Change → EventBridge**
  - Lambda pulls recent log lines from a CloudWatch log group
  - Lambda calls OpenAI and writes a JSON summary to **S3**, metadata to **DynamoDB**, and publishes a short alert to **SNS**

### Layer 2 — Application Delivery (Project 2)
Core components:
- Dockerized web app
- ECR repository
- ECS Fargate service behind an ALB
- GitHub Actions workflow:
  - build image
  - push to ECR (SHA + `latest`)
  - force new ECS deployment

> Note: this pipeline triggers redeploys; it does not currently register a new task definition revision pinned to the SHA image.

### Layer 3 — Governance / Ops (Project 3)
What’s in place:
- Organization enabled and visible
- IAM roles/policies related to governance and automation
- GuardDuty / Security Hub / CloudTrail / AWS Config visibility screenshots
- A simple governance dashboard site (S3 website)

Planned next (not delivered yet):
- member accounts (Security/Dev/Prod) + OU structure
- SCP guardrails applied at OU/account scope
- AI incident assistant pipeline (event → summary → storage/notifications)

---

## How to run this repo

Each project has its own README with exact commands and verification steps:
- Project 1 README: deploy/verify/destroy + AI summary evidence
- Project 2 README: deploy/verify + workflow reference
- Project 3 README: governance evidence + what is planned vs implemented

---

## Operational notes (what I’m optimizing for)

This platform is written with an operator mindset:
- clear “verify health” checks (ALB target health, ECS service health, RDS status, alarms)
- screenshots that prove the environment exists
- destroy paths to prevent runaway spend

---

## Cost awareness (high-level)

Typical cost drivers in these projects:
- NAT Gateway hourly + data processing
- ALB hourly + LCUs
- ECS task CPU/memory-hours
- RDS instance + storage + backups
- CloudWatch log ingestion + retention
- AI summaries only run on alarm state changes (event-driven)

---

## Future enhancements (kept separate on purpose)

- Task-definition pinning + rollback flow in CI/CD
- Basic unit tests and container scans in the pipeline
- Multi-account buildout with delegated admin + aggregation
- Ticket/Slack integration for incident summaries
- Policy-as-code and IaC testing

---

## Contact

Josh Holman  
Infrastructure Engineer • Cloud Operations  

LinkedIn: https://www.linkedin.com/in/jnholmanjr/  
Email: jnholman@charter.net/

