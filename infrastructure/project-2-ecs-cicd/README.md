# Project 2 — Container Platform & CI/CD (Application Delivery Layer)

Project 2 moves the RSVP app from VM-style deployment to containers on ECS Fargate, with an automated GitHub Actions workflow that builds SHA-tagged immutable images, pushes to ECR, and deploys via ECS rolling service updates.

---

## Deployment

**Status:** Portfolio (torn down — originally deployed 2026-02-02)

Evidence: see [`./evidence/`](./evidence/) for screenshots, deployment outputs, and GitHub Actions logs.

---

## Overview

This project includes:

* **Dockerized RSVP web application** (Python + Flask)
* **Amazon ECR repository** for container images with SHA-based tagging
* **ECS Fargate cluster/service** behind an Application Load Balancer
* **Production-grade GitHub Actions workflow** that:
  * Builds the Docker image
  * Tags with Git commit SHA (immutable, auditable)
  * Pushes to ECR
  * Downloads the current task definition and registers a new revision with the SHA-tagged image
  * Updates the ECS service and waits for stabilization

This repo demonstrates a practical "small team" delivery path: standard runtime, repeatable builds, immutable deployments, and automated releases without managing Kubernetes.

---

## Business Problem

RSVP Society needs to ship updates quickly without manual SSH deploys and "works on my machine" issues. Containers + ECS provide a consistent runtime, and GitHub Actions automates the release steps with full traceability via Git SHAs.

---

## Architecture Breakdown

### Containerization
- App packaged as a single-stage Docker image (`python:3.12-slim` + gunicorn)
- Local build supported for dev/testing

### Image Registry (ECR)
- ECR stores images with SHA-based tags
- Each commit gets unique, immutable image tag
- Example: `852121054175.dkr.ecr.us-east-1.amazonaws.com/rsvp-project2-app:9ff0fa4`
- Enables exact version tracking and rollbacks

### ECS Fargate
- ECS cluster runs service on Fargate (no EC2 instance management)
- Task definition: 256 CPU units (0.25 vCPU), 512 MiB memory
- Service attached to ALB target group
- Health checks automatically remove unhealthy tasks
- Rolling deployment strategy (ECS replaces tasks in-place)

### Network placement (demo mode)
- ECS tasks run in **public subnets** with `assign_public_ip = true` so Fargate can pull images from ECR without a NAT Gateway
- For production, tasks would move to private subnets behind a NAT Gateway or use VPC endpoints for ECR/CloudWatch/S3

### Load Balancing
- Application Load Balancer (internet-facing)
- HTTP listener on port 8080
- Target group with health checks
- Distributes traffic across healthy ECS tasks

### CI/CD (GitHub Actions)

**Workflow file:** `.github/workflows/ecs-project2-deploy.yml`

**Pipeline steps:**

1. **Trigger:** Pushes to `main` affecting `infrastructure/project-2-ecs-cicd/`
2. **Build:** Docker image with Git SHA tag
3. **Push:** Image to ECR with immutable SHA tag
4. **Download:** Current ECS task definition
5. **Update:** Task definition JSON with new image SHA
6. **Register:** New task definition revision
7. **Deploy:** Update ECS service with new task definition
8. **Verify:** Wait for service to stabilize

**Key features:**
- ✅ Immutable SHA-tagged images (no mutable `latest` tag)
- ✅ New task definition revision per deploy
- ✅ Rolling deployment with health-check gating (not `--force-new-deployment`)
- ✅ Deployment verification (waits for service stability)
- ✅ Full audit trail (Git SHA = exact code version)
- ✅ Rollback capability (deploy any previous SHA)
- ✅ OIDC-based keyless AWS auth (no static IAM keys)
- ✅ Git SHA injected into `APP_VERSION` env var at deploy time

### Version traceability
Docker images are SHA-pinned and each deploy creates a new task definition revision. The CI/CD workflow injects the short Git SHA into the `APP_VERSION` environment variable at deploy time, so the version displayed in the app UI matches the exact commit that was deployed.

---

## Verify (Fast Checks)

**Infrastructure:**
- ✅ ECR: Repository contains SHA-tagged images
- ✅ ECS Cluster: 1 service active, 1 task running
- ✅ ECS Service: Desired count matches running count
- ✅ Task Definition: References SHA-tagged image
- ✅ Target Group: Targets are healthy
- ✅ ALB: Live URL returns HTTP 200 with rendered UI

**Deployment Traceability:**
- ✅ Image tag in ECR matches Git commit SHA
- ✅ Task definition revision tracks each deployment
- ✅ GitHub Actions logs show exact image deployed

---

## Cost Notes

**Estimated monthly cost:** ~$30-40 (us-east-1, single task, demo mode)

Primary costs:
- **Fargate:** ~$10/month (0.25 vCPU, 512 MB, 24/7)
- **ALB:** ~$16/month (hourly + LCUs)
- **ECR Storage:** ~$1/month
- **CloudWatch Logs:** ~$2/month

Production mode would add NAT Gateway (~$32/month) or VPC endpoints for private subnet placement.

---

## Deployment History

**Recent deployments:**
- **Latest:** SHA-pinned deployment with new CI/CD workflow
- **v1.0.4-ci:** Previous mutable-tag deployment
- **v1.0.3-ci:** Earlier version
- **v1.0.2-ci:** Initial automated deployment

All deployments tracked via GitHub Actions with full logs.

---

## What This Demonstrates

**Modern Container Delivery:**
- Serverless compute (Fargate — no EC2 management)
- Immutable infrastructure (SHA-tagged images)
- Automated deployments with verification

**DevOps Best Practices:**
- Infrastructure as Code (Terraform)
- CI/CD automation (GitHub Actions)
- SHA-based versioning (full audit trail, reflected in app UI)
- OIDC-based keyless AWS authentication
- Rolling deployments with health gating
- Health check monitoring (automatic recovery)

**Production Readiness:**
- Load balancer redundancy
- Container isolation
- Automated rollouts
- Health-based routing
- Rollback capability

---

## 📸 Infrastructure Screenshots

### CI/CD Pipeline
![GitHub Actions Workflow](./evidence/screenshots/cicd-pipeline-run.png)  
*Successful automated deployments with build, push, and deploy steps*

### Container Registry
![ECR Repository](./evidence/screenshots/ecr-repository.png)  
*Amazon ECR with SHA-tagged container images*

### ECS Infrastructure
![ECS Cluster](./evidence/screenshots/ecs-cluster-overview.png)  
*ECS Fargate cluster with active service*

![ECS Service Overview](./evidence/screenshots/ecs-service-overview.png)  
*Service configuration and deployment status*

![ECS Service Health](./evidence/screenshots/ecs-service-health.png)  
*Service health metrics and target status*

### Task Configuration
![Task Definition](./evidence/screenshots/ecs-task-definition.png)  
*Task definition with CPU, memory, and container settings*

### Load Balancing
![ALB Overview](./evidence/screenshots/ecs-alb-overview.png)  
*Application Load Balancer configuration*

![Target Group](./evidence/screenshots/ecs-target-group.png)  
*Target group with healthy ECS tasks*

### Application
![Live Application](./evidence/screenshots/project2-ui.png)  
*Containerized application interface*

---

## Future Enhancements (Planned)

- [ ] HTTPS with ACM certificate and custom domain
- [ ] Private subnet placement with NAT Gateway or VPC endpoints
- [ ] Container image scanning (Trivy/Grype) in CI/CD
- [ ] Multi-stage Docker build for smaller image
- [ ] Unit tests in GitHub Actions workflow
- [ ] Staging environment with approval gates
- [ ] Auto-scaling policies based on CPU/memory

---

## Technical Stack

- **Container Runtime:** Docker
- **Orchestration:** AWS ECS Fargate
- **Registry:** Amazon ECR
- **Load Balancing:** AWS Application Load Balancer
- **CI/CD:** GitHub Actions
- **Infrastructure:** Terraform
- **Application:** Python + Flask
- **Networking:** AWS VPC (public subnets in demo mode)

---

**Author:** Josh Holman  
**Last Updated:** February 2, 2026  
**Region:** us-east-1
