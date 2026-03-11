# Project 2 — RSVP Cloud Service (ECS Container Platform)

**Deployment Date:** December 3, 2025  
**Status:** Portfolio (torn down — evidence captured at time of deployment)

---

## Infrastructure Overview

This folder contains evidence of a complete, working containerized application deployment using AWS ECS Fargate with automated CI/CD.

### Resources Deployed

| Resource Type | Resource ID/Name | Status |
|---------------|------------------|--------|
| ECS Cluster | `rsvp-project2-cluster` | ✅ Active |
| ECS Service | `rsvp-project2-service` | ✅ 1 task running |
| Task Definition | `rsvp-project2-task:4` | ✅ Active |
| Application Load Balancer | `rsvp-project2-alb` | ✅ Active (1 healthy target) |
| Target Group | `rsvp-project2-tg` | ✅ 1 healthy target |
| ECR Repository | `rsvp-project2-app` | ✅ Active (multiple SHA-tagged images) |
| VPC | `vpc-09569aec0c1b01114` | ✅ Active |
| GitHub Actions Workflow | `ECS Project 2 - Build & Deploy` | ✅ 5 successful runs |

---

## Live Endpoints

**Application URL:**  
http://rsvp-project2-alb-901306910.us-east-1.elb.amazonaws.com:8080

**Service Version:** v1.0.4-ci

---

## Screenshots

### CI/CD Pipeline

1. **`cicd-pipeline-run.png`** - GitHub Actions workflow showing 5 successful deployments
   - Latest: "Bump ECS app version to v1.0.4-ci" (Dec 3, 11:25 PM EST)
   - All builds completed in 23-36 seconds
   - Automated on every push to main branch

### Container Registry

2. **`ecr-repository.png`** - Amazon ECR repository with container images
   - Repository: `rsvp-project2-app`
   - Multiple SHA-tagged immutable images
   - Encrypted with AES-256

### ECS Infrastructure

3. **`ecs-cluster-overview.png`** - ECS cluster dashboard
   - 1 service running
   - 1 task running
   - 0 EC2 instances (Fargate serverless)

4. **`ecs-service-overview.png`** - ECS service details
   - Service: `rsvp-project2-service`
   - Launch type: FARGATE
   - Task definition: `rsvp-project2-task:4`
   - Deployment status: Success (1 completed deployment)

5. **`ecs-service-health.png`** - Service health and metrics
   - Status: Active
   - Tasks: 1 Desired, 0 Pending, 1 Running
   - Load balancer: 1 Healthy target
   - Container Insights enabled

6. **`ecs-task-definition.png`** - Task definition configuration
   - CPU: 256 units (0.25 vCPU)
   - Memory: 512 MiB
   - Container: Python + Flask application
   - Image source: ECR with SHA digest

### Load Balancing

7. **`ecs-alb-overview.png`** - Application Load Balancer configuration
   - ALB: `rsvp-project2-alb`
   - Scheme: Internet-facing
   - Availability Zones: us-east-1a (uest-az1), us-east-1b (uest-az6)
   - DNS: rsvp-project2-alb-901306910.us-east-1.elb.amazonaws.com

8. **`ecs-target-group.png`** - Target group health
   - Target group: `rsvp-project2-tg`
   - Protocol: HTTP:8080
   - 1 healthy target (10.20.1.166:8080)
   - Health check path: /

### Application

9. **`project2-ui.png`** - Live application interface
   - Title: "RSVP Cloud Service"
   - Description: "Containerized RSVP microservice running behind an Application Load Balancer in ECS Fargate"
   - Displays: Region, Runtime, Images, Deployments, Logs, Metrics, AI integration
   - Interactive: API message endpoint test functionality

---

## Verification Results

### ✅ Container Platform
- ECS Fargate cluster operational
- Service maintaining desired count (1 task)
- Task definition revision 4 active
- Container running Python + Flask application

### ✅ CI/CD Pipeline
- GitHub Actions workflow automated
- Builds triggered on every push to main
- Docker image build and push to ECR
- ECS task definition updated
- Service deployment triggered
- All 5 workflow runs successful

### ✅ Networking & Load Balancing
- ALB accepting HTTP traffic on port 8080
- Target group health checks passing
- Single healthy target registered
- DNS resolution working

### ✅ Container Registry
- ECR repository storing images
- SHA-based immutable tagging
- Image encryption enabled
- Multiple image versions available

### ✅ Security
- VPC networking configured
- Security groups properly scoped
- Private registry (ECR)
- Task execution role with minimal permissions

---

## Architecture Highlights

**Serverless Container Platform:**
- No EC2 instances to manage
- ECS Fargate handles infrastructure
- Auto-scaling ready (currently 1 task)

**Immutable Deployments:**
- SHA-tagged container images
- Version tracking via Git commits
- Automated rollout via GitHub Actions

**Network Architecture (demo mode):**
- ALB in public subnets (internet-facing)
- ECS tasks in public subnets with public IP (no NAT Gateway needed)
- Production mode would move tasks to private subnets behind NAT or VPC endpoints

**CI/CD Automation:**
- Build: Docker image creation
- Push: ECR repository upload
- Deploy: ECS task definition update
- Rollout: Service deployment trigger

---

## Deployment Workflow

1. **Code Push:** Developer pushes to `main` branch
2. **Build Trigger:** GitHub Actions workflow starts
3. **Docker Build:** Application containerized
4. **ECR Push:** Image tagged with SHA and pushed
5. **Task Update:** ECS task definition updated with new image
6. **Service Deploy:** ECS service rolls out new task
7. **Health Check:** ALB verifies target health
8. **Traffic Shift:** New task receives traffic

**Average deployment time:** 30-35 seconds (from push to live)

---

## Technical Implementation

**Container Orchestration:**
- AWS ECS Fargate (serverless)
- Task CPU: 256 units (0.25 vCPU)
- Task Memory: 512 MiB
- Launch type: FARGATE

**Application:**
- Runtime: Python + Flask
- Port: 8080
- Health endpoint: `/`
- API endpoint: `/api/message`

**Infrastructure as Code:**
- Terraform managed
- VPC, ALB, ECS cluster, ECR repository
- Task definitions versioned

**CI/CD:**
- GitHub Actions
- Docker single-stage builds
- Automated deployments
- SHA-based versioning

---

## Cost Summary

**Estimated Monthly Cost:** ~$15-20 (us-east-1, single task)

| Service | Monthly Cost |
|---------|--------------|
| ECS Fargate (1 task, 0.25 vCPU, 512 MB) | ~$10 |
| ALB | ~$16 |
| ECR Storage | ~$1 |

**Cost Optimization:**
- Single task deployment (development)
- Minimal Fargate sizing
- Can scale to zero when not in use (manual)

---

## Deployment History

**Version Timeline:**
- **v1.0.4-ci** - Latest (Dec 3, 2025, 11:25 PM EST)
- **v1.0.3-ci** - Dec 3, 2025, 8:19 PM EST
- **v1.0.2-ci** - Dec 3, 2025, 8:11 PM EST
- **v1.0.1** - Initial ECS deployment (Dec 3, 2025, 7:42 PM EST)

All deployments successful, demonstrating reliable CI/CD pipeline.

---

## What This Demonstrates

**Modern Container Delivery:**
- Microservices architecture
- Serverless compute (Fargate)
- Immutable infrastructure
- Automated deployments

**DevOps Best Practices:**
- Infrastructure as Code
- CI/CD automation
- SHA-based versioning
- Health check monitoring

**Production Readiness:**
- Load balancer redundancy
- Container isolation
- Automated rollouts
- Health-based routing

---

**Evidence collected by:** Josh Holman  
**Deployment tool:** Terraform + GitHub Actions  
**AWS Region:** us-east-1  
**Date:** December 3, 2025
