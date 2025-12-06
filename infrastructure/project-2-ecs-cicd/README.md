A fully containerized microservice deployed on Amazon ECS Fargate, fronted by an Application Load Balancer, and automatically built & deployed via GitHub Actions CI/CD.

Live Service URL:
👉 http://rsvp-project2-alb-901306910.us-east-1.elb.amazonaws.com:8080

The UI provides:

Service environment details

Runtime metadata

Deployment info from GitHub

Future AI integration hooks

Test interface for /api/message endpoint

🚀 Overview

RSVP Cloud Service is a Python/Flask microservice designed to show real-world cloud deployment workflows:

GitHub → build Docker image → push to ECR → deploy to ECS Fargate

ALB handles traffic on port 8080

Tasks run in a secure VPC using awsvpc networking

Load balancer health checks monitor /health

CloudWatch logs automatically capture runtime output

This project demonstrates real production-level DevOps workflows with zero manual server work.

🧱 Architecture
Layer	Service	Purpose
Compute	ECS Fargate	Serverless container runtime
CI/CD	GitHub Actions	Automated build → test → deploy
Container Registry	ECR	Stores versioned Docker images
Networking	ALB (HTTP 8080)	Routes external traffic to tasks
Logging	CloudWatch Logs	Per-task application logs
Security	IAM Task Roles	Least-privilege access model
🛰️ Key Features
✔ Containerized microservice

Built with Python + Flask and packaged via Docker.

✔ GitHub Actions CI/CD

On every push, GitHub builds the image

Tags it with Git SHA

Pushes to ECR

Re-deploys the ECS Service

Zero downtime, rolling updates

✔ Load-balanced HA deployment

ALB → Target Group → Fargate task.

✔ Observability

CloudWatch Logs

ECS Service metrics (CPU, memory, running tasks)

✔ AI-Ready Hooks

The UI includes placeholders for future:

AI-based service insights

Automated incident analysis

Intelligent debugging assistant
