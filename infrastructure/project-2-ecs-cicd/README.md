RSVP Containerized App Platform – Project 2

Fully automated container deployment pipeline for RSVP Society’s event platform.
Built with AWS ECS Fargate, ECR, ALB, and GitHub Actions.

Live Service URL:
👉 http://rsvp-project2-alb-901306910.us-east-1.elb.amazonaws.com:8080

📌 Business Problem

As the RSVP platform grows, relying on EC2 user_data deployments becomes limiting:

Manual deployments slow down feature releases

Hard to coordinate updates across multiple app servers

Inconsistent build environments

Increased operational overhead

No automated rollback or versioning

Growing businesses need:

Containerization

Continuous delivery pipelines

Zero-downtime deployments

Secure, repeatable build processes

🎯 Business Solution

Project 2 delivers a production-ready container platform that automates the entire build → deploy lifecycle.

⭐ Containerization

Application packaged into a Docker image

Stored in private Amazon ECR repository

Each commit automatically builds a clean image

⭐ Fully Managed Compute

ECS Fargate runs the container with NO servers to manage

Auto-healing ensures 24/7 availability

ALB routes traffic to healthy tasks

⭐ Continuous Deployment via GitHub Actions

Whenever code is pushed to main:

GitHub Actions builds a Docker image

Logs into ECR

Pushes the new image

Triggers ECS task definition update

ECS performs rolling deployment with zero downtime

Releases are automatic, safe, and consistent.

🏗 Architecture Overview
1. Networking

Reuses Project 1 VPC

Private subnets for ECS tasks

Public subnets for ALB

IAM roles for ECS tasks + execution

2. Container Layer

Dockerfile builds app image

Amazon ECR stores multiple tagged versions

3. Compute

ECS Cluster (serverless Fargate compute)

ECS Service with:

Desired count (1–2 tasks)

Rolling deployment controller

ECS Task Definition referencing your ECR image

4. Load Balancing

ALB routes to Fargate tasks

Health checks ensure only healthy tasks receive traffic

5. CI/CD Pipeline

GitHub Actions workflow:

Checks out repo

Builds Docker image

Logs into AWS ECR

Pushes image

Updates ECS service

Triggers rollout

🧩 Technology Stack
Layer	Technology
IaC	Terraform
Containers	Docker
Container Registry	Amazon ECR
Compute	ECS Fargate
Networking	ALB, VPC
CI/CD	GitHub Actions
IAM	Task roles + execution roles
🚦 Deployment
1️⃣ Build infrastructure (Terraform)
terraform init
terraform apply

2️⃣ Push application code

Just push commits to main — the pipeline deploys automatically.

📸 Demo

Push code → ECS updates automatically

ALB DNS instantly serves new container version

Zero downtime

(Add screenshots of ECS console + ALB test page here.)

🔮 Future Enhancements
1. Blue/Green Deployments

Safer releases using CodeDeploy + ECS

2. Canary Deployments

Send 1–5% of traffic to new versions first

3. Secrets Manager Integration

Secure DB credentials, API keys

4. Autoscaling

Scale ECS tasks based on CPU, memory, request count

5. Logging & Monitoring

CloudWatch Logs + Datadog or OpenSearch

💼 Business Value Summary

This project demonstrates:

Modern container architecture

Production-ready CI/CD automation

Immutable deployments

Cost-efficient and fully managed compute

Zero-downtime rollouts

It prepares RSVP Society’s platform for real growth and rapid feature iteration.
