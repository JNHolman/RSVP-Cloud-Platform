# RSVP Cloud Platform

A multi-project AWS lab showing real-world Cloud / DevOps / SRE skills, built around an event-booking concept called **RSVP**.

This repo contains multiple infrastructure projects under [`infrastructure/`](./infrastructure):

- **Project 1 – Cloud Platform (Terraform + EC2 + RDS)**  
  Highly available, cost-optimized AWS infrastructure for a small event-booking platform.  
  Implements VPC, public/private subnets, NAT, ALB, EC2 app servers, RDS, IAM hardening, and basic monitoring.

- **Project 2 – ECS Fargate App + CI/CD Pipeline**  
  Containerized Python/Flask service running on ECS Fargate behind an ALB, with Docker images in ECR and a GitHub Actions pipeline that builds, pushes, and deploys on every `git push`.

---

## Project 1 – Cloud Platform (infrastructure/project-1-cloud-platform)

**Tech stack**

- AWS: VPC, Subnets, Internet Gateway, NAT Gateway  
- EC2 app instances behind an Application Load Balancer  
- RDS (PostgreSQL) in private subnets  
- Security Groups, IAM roles and instance profiles  
- CloudWatch metrics and alarms, SNS notifications  
- Terraform for full Infrastructure as Code

**What this shows**

- Designing a secure, multi-tier VPC (public web, private data)
- Using ALB + EC2 for a highly available application tier
- Managing relational databases in AWS with RDS
- Applying least-privilege IAM and security groups
- Managing infra lifecycle with Terraform (`terraform init/plan/apply`)

---

## Project 2 – ECS Fargate + CI/CD (infrastructure/project-2-ecs-cicd)

**App**

- Python Flask service with:
  - `/health` endpoint for ALB/ECS health checks  
  - `/api/message` JSON endpoint  
  - Simple UI showing version, environment, and platform info

**Infrastructure**

- AWS ECS Fargate service running containers from ECR
- Application Load Balancer + target group + health checks
- CloudWatch Logs for container logs
- IAM task role & execution role
- Terraform modules for VPC, ECS, ALB, IAM, logging

**CI/CD**

- Dockerfile builds a production image with Gunicorn
- GitHub Actions workflow:
  - Triggers on changes under `infrastructure/project-2-ecs-cicd/**`
  - Builds Docker image and tags with `GITHUB_SHA`
  - Pushes image to Amazon ECR
  - Updates ECS service and forces a new deployment
- Effect: `git push` → new version automatically deployed to Fargate with zero downtime

**What this shows**

- Containerizing apps with Docker
- Running serverless containers on ECS Fargate
- Managing infrastructure with Terraform
- Building CI/CD pipelines with GitHub Actions
- Using ECR as a private Docker registry
- Rolling deployments with ALB health checks

---

## How to run locally (Project 2 app)

```bash
cd infrastructure/project-2-ecs-cicd/app
pip3 install -r requirements.txt
python3 app.py   # runs on http://127.0.0.1:8080


Author

Josh Holman
Cloud & Network Engineer
Louisville, KY
