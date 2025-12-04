🚀 RSVP Cloud Platform — Modern AWS Infrastructure & DevOps Portfolio

A multi-project cloud engineering platform built around a simple business concept: RSVP Society, a scalable event-driven brand that needs secure infrastructure, reliable APIs, and fast deployments.

This repo contains two end-to-end production-grade cloud systems, each solving real business problems using modern AWS architecture, Infrastructure-as-Code, CI/CD automation, and AI-powered monitoring.

🧩 Business Scenario

RSVP Society is a growing event brand that needs:

A secure, reliable cloud platform to host event data

A scalable application backend that can handle traffic spikes

Automated deployments so changes ship quickly without downtime

Monitoring + alerting so issues are caught immediately

AI-powered diagnosis to reduce troubleshooting time

This repo demonstrates exactly how a Cloud/DevOps/SRE engineer would architect and operate that platform.

📦 Repository Structure
infrastructure/
│
├── project-1-cloud-platform/      # Traditional VPC + ALB + EC2 + RDS infrastructure
├── project-2-ecs-cicd/            # ECS Fargate microservice + CI/CD pipeline
│
.github/workflows/                 # Automated GitHub Actions pipelines
README.md
LICENSE

🧱 PROJECT 1 — Cloud Platform (VPC + EC2 + RDS + AI Logs)

Folder: infrastructure/project-1-cloud-platform

🎯 Business Problem

The company needs a secure cloud foundation to run applications and store customer data.
It must be:

Highly available

Private where required

Cost-optimized

Fully managed via IaC

Observable and auditable

This mirrors what real small-to-medium businesses need when they migrate to AWS.

🏗 Architecture Overview

AWS Components:

VPC with public + private subnets

Internet Gateway & NAT Gateway

Route Tables + Associations (public → IGW, private → NAT)

EC2 Application Server (private subnet)

Application Load Balancer (public subnet)

RDS PostgreSQL (multi-AZ capable private DB)

IAM Instance Role & Policies

CloudWatch Metrics + Alarms

SNS Email Alerts (high CPU, unhealthy host, DB connection drops)

AI-Powered Log Diagnostics (Lambda + OpenAI)

🤖 AI Component — Automated Incident Diagnosis

Files:

ai-logs.tf

lambda_function.py

ai_lambda_package.zip

What the AI does:

Monitors EC2 application logs (CloudWatch Logs)

When errors occur, Lambda is triggered

Lambda fetches recent error lines

Sends them to OpenAI for analysis

AI returns:

probable root cause

recommended fix

severity level

Lambda stores summary in S3 and/or sends via SNS email

Business Value

Dramatically reduces time-to-diagnosis

Helps small teams operate like large SRE orgs

Provides auto-generated postmortems

🧱 PROJECT 2 — ECS Fargate Microservice + CI/CD Pipeline

Folder: infrastructure/project-2-ecs-cicd

🎯 Business Problem

As RSVP grows, the company needs:

A scalable API tier

Decoupled services (microservices)

Zero-downtime deployments

Repeatable and automated builds

Lower operational burden than EC2

Faster release cycles

This project solves that by moving infrastructure to containers and serverless compute.

🏗 Architecture Overview

AWS Components:

ECS Fargate Cluster (serverless containers)

ECR Repository for Docker images

ALB + Target Group for HTTP routing

CloudWatch Logs for container output

SSM Parameter Store for environment variables

IAM Task Role + Execution Role

App Functionality:

/health endpoint for ALB health checks

/api/message endpoint

UI page that shows active app version

Gunicorn production server

🔄 CI/CD Pipeline (GitHub Actions → ECR → ECS)

Every push triggers:

Docker Build

Tag Image with Git Commit SHA

Push to ECR

Deploy to ECS Service

Zero-downtime rolling update

This mirrors real enterprise CI/CD pipelines (GitHub Actions → AWS).

Business Value

Rapid release cycles

No manual deployment steps

Scalable microservices

Consistent environment across dev → prod

Developer velocity increases
Author

Josh Holman
Cloud & Network Engineer
Louisville, KY
