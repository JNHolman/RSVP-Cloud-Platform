# Project 1 — RSVP Cloud Platform (Infrastructure Layer)

Project 1 builds the foundational AWS infrastructure for a small web application: networking, ingress, compute scaling, database, alerting, and an event-driven AI log summary workflow. This is a **production-style lab**: deployable, verifiable, and designed to be destroyed cleanly to control cost.

---

## 🚀 Deployment Status

**Status:** ✅ **Live and Operational** (Deployed: February 2, 2026)

### Live Endpoints
- **Application:** http://rsvp-dev-alb-1273619337.us-east-1.elb.amazonaws.com/
- **Health Check:** http://rsvp-dev-alb-1273619337.us-east-1.elb.amazonaws.com/health

### Deployed Resources
| Resource | Identifier | Status |
|----------|-----------|--------|
| VPC | `vpc-06b57ae331224b367` | ✅ Active |
| Public Subnets | 2 across us-east-1a/1b | ✅ Active |
| Private Subnets | 2 across us-east-1a/1b | ✅ Active |
| Application Load Balancer | `rsvp-dev-alb` | ✅ Active |
| Auto Scaling Group | `rsvp-dev-asg` | ✅ 2 healthy instances |
| RDS MySQL | `rsvp-dev-db` | ✅ Available |
| Lambda (AI Summarizer) | `rsvp-dev-ai-log-summarizer` | ✅ Active |
| S3 Bucket (AI Logs) | `rsvp-dev-ai-logs` | ✅ Active |
| DynamoDB Table | `rsvp-dev-ai-log-summaries` | ✅ Active |
| CloudWatch Alarms | Multiple | ✅ Configured |

**Evidence:** See [`evidence/`](./evidence/) folder for deployment screenshots and outputs.

---

## Overview

This project provisions AWS infrastructure with **Terraform**:

- Multi-AZ VPC with public and private subnets
- Application Load Balancer (ALB)
- EC2 Auto Scaling Group for the web tier
- RDS MySQL in private subnets
- Internet Gateway + NAT Gateway + route tables
- Security groups scoped by tier (ALB → app → DB)
- CloudWatch alarms and log group (app logs)
- SNS alerts topic (email subscription optional)
- AI log summarization workflow:
  - **CloudWatch alarm actions → SNS email alerts**
  - **CloudWatch Alarm State Change → EventBridge → Lambda → OpenAI → S3 + DynamoDB → SNS**

This is a common baseline pattern for teams moving off a single server into AWS with predictable operations and a clear failure/alert path.

---

## Architecture diagram

![Project 1 Network Architecture](./evidence/screenshots/vpc-overview.png)

---

## Business problem

RSVP apps and event sites tend to spike during promos and major weekends. A single instance/VPS is a single point of failure. This project shows a baseline architecture that:

- scales the web tier horizontally
- keeps the database isolated in private subnets
- alerts on obvious failure signals (ALB 5xx, high CPU)
- produces a short, human-readable summary when an alarm fires

---

## Key design decisions

- **Multi-AZ VPC** to reduce single-AZ blast radius
- **ALB + Auto Scaling Group** instead of one EC2 instance
- **RDS MySQL in private subnets** for managed storage and isolation
- **Public subnets for ALB; private subnets for app/DB**
- **CloudWatch alarms + SNS** for alerts (no silent failures)
- **Event-driven AI summaries** only when alarms change state (no polling)

---

## Architecture breakdown

### Networking
- 1 VPC (`10.0.0.0/16`)
- Public subnets (`10.0.1.0/24`, `10.0.2.0/24`) - ALB, NAT
- Private subnets (`10.0.3.0/24`, `10.0.4.0/24`) - app tier, DB tier
- Internet Gateway attached to the VPC
- NAT Gateway for private subnet egress
- Separate route tables for public/private traffic flows

### Compute & load balancing
- ALB (HTTP listener on port 80)
- Target group routes to instances in an Auto Scaling Group
- ASG: min=2, max=4, desired=2 (t3.micro instances)
- Health checks: `/health` endpoint

### Database
- RDS MySQL instance (db.t3.micro)
- Private subnets only (no public access)
- DB security group allows inbound only from the app tier security group
- Automated backups handled by RDS

### Monitoring & alerts
- CloudWatch alarms:
  - ALB 5xx high (threshold: 5 errors/minute)
  - ASG average CPU high (threshold: 75%)
  - Lambda errors (optional)
- SNS topic for alerting (email subscription: jholman@charter.net)

---

## AI log summarization (✅ Implemented)

This project includes an event-driven summary workflow that turns an alarm + a short slice of recent logs into a stored JSON summary and a short notification.

### Trigger paths (two things happen)
1) **Alerting:** CloudWatch alarm actions publish to **SNS** (email subscription configured).  
2) **Summaries:** CloudWatch alarm state changes are matched by an **EventBridge rule**, which invokes the summarizer Lambda.

### Summary workflow
**CloudWatch Alarm State Change → EventBridge → Lambda → OpenAI → S3 + DynamoDB → SNS**

What the Lambda does:
- Pulls the last ~5 minutes of log lines from the app log group (`/rsvp-dev/app`)
- Calls OpenAI (gpt-4o-mini) with the alarm details + recent logs
- Writes a full JSON record to S3: `summaries/<uuid>.json`
- Writes metadata to DynamoDB (id, timestamp, alarm, state, s3_key)
- Publishes a short message to SNS

### Real-world example
The system captured and processed an actual ALB alarm state change:
- Alarm: `rsvp-dev-alb-5xx-high` changed to `OK`
- Lambda executed successfully
- Summary stored in S3: `summaries/c0651d8e-be49-4ac1-a75a-e03d9d7da8a3.json`
- Metadata recorded in DynamoDB

### Guardrails (what this does and does not do)
- No auto-remediation. Output is summaries + suggestions only.
- Scoped context: alarm metadata + recent logs only.
- Fail-safe: if the model call fails, it records the error and still writes the record.
- Event-driven: runs on alarm state changes, not continuously.

---

## Quick Start

### Prerequisites
- Terraform >= 1.0
- AWS CLI configured with credentials
- OpenAI API key (for AI summarization)

### Deploy

```bash
# 1. Configure variables
cp terraform.tfvars.example terraform.tfvars
# Edit: openai_api_key, alert_email, db_password

# 2. Initialize Terraform
terraform init

# 3. Preview changes
terraform plan

# 4. Deploy
terraform apply

# 5. Get outputs
terraform output
```

### Verify

```bash
# Check ALB health
curl $(terraform output -raw alb_http_url)
curl $(terraform output -raw alb_health_url)

# Check target health
aws elbv2 describe-target-health \
  --target-group-arn $(aws elbv2 describe-target-groups \
    --names rsvp-dev-tg \
    --query 'TargetGroups[0].TargetGroupArn' \
    --output text)

# Check RDS status
aws rds describe-db-instances \
  --db-instance-identifier rsvp-dev-db \
  --query 'DBInstances[0].DBInstanceStatus'
```

### Destroy

```bash
terraform destroy
```

---

## Verify (fast checks)

**Infrastructure**
- ✅ ALB target group shows **healthy** targets (2/2)
- ✅ ASG instances are **InService** (2 instances running)
- ✅ RDS status is **Available**
- ✅ CloudWatch alarms exist and are **OK**

**AI summaries**
- ✅ EventBridge rule routing alarms to Lambda
- ✅ Lambda successfully executing (Python 3.10)
- ✅ S3 bucket contains summary objects
- ✅ DynamoDB table contains summary metadata
- ✅ SNS notifications configured

---

## Cost strategy (practical)

**Estimated monthly cost:** ~$80-90 (us-east-1, dev sizing)

Primary cost drivers in this stack:
- NAT Gateway: ~$32/month (hourly + data processing)
- ALB: ~$16/month (hourly + LCUs)
- EC2 instances: ~$14/month (t3.micro × 2)
- RDS: ~$15/month (db.t3.micro + storage)
- CloudWatch logs: ~$5/month (ingestion + retention)
- Lambda/S3/DynamoDB: ~$5/month
- AI calls: Minimal (only on alarm state changes)

**Cost control:** Terraform makes it easy to spin the environment up for demos/tests and destroy it afterward with `terraform destroy`.

---

## Security

**Current implementation (development):**
- HTTP only (no HTTPS)
- Security groups follow least-privilege principle
- RDS in private subnets (no public access)
- DB password in terraform.tfvars (gitignored)

**Production improvements:**
- [ ] HTTPS termination with ACM certificate
- [ ] WAF rules for application protection
- [ ] Secrets Manager for DB credentials and API keys
- [ ] Enhanced IAM roles (more specific resource ARNs)
- [ ] VPN/Direct Connect for administrative access
- [ ] Multi-region failover

---

## Future enhancements (planned)
- HTTPS termination on ALB using ACM
- WAF rules for basic protections
- SSM Parameter Store / Secrets Manager integration
- Expand summaries to include trends (not just alarm events)
- Slack/Teams notifications
- Auto-scaling policies based on metrics
- Enhanced monitoring dashboard

---

## 📸 Infrastructure screenshots (evidence)

All screenshots and deployment artifacts are in the [`evidence/`](./evidence/) folder.

### VPC & Networking
![VPC Overview](./evidence/screenshots/vpc-overview.png)  
![Subnets List](./evidence/screenshots/subnets-list.png)

### Load Balancing
![ALB Overview](./evidence/screenshots/alb-overview.png)  
![Target Group](./evidence/screenshots/target-group.png)

### Compute
![Auto Scaling Group](./evidence/screenshots/autoscaling-group.png)

### Database
![RDS Overview](./evidence/screenshots/rds-overview.png)

### Monitoring & AI Automation
![CloudWatch Alarms](./evidence/screenshots/cloudwatch-alarms.png)  
![Lambda Log Summarizer](./evidence/screenshots/lambda-function.png)

### Storage (AI Log Summaries)
![S3 Bucket Overview](./evidence/screenshots/s3-bucket-overview.png)  
![S3 Summary Object](./evidence/screenshots/s3-summary-object.png)

### Application UI
![Project UI](./evidence/screenshots/project-ui.png)

---

## Technical Stack

- **Infrastructure as Code:** Terraform
- **Compute:** AWS EC2 (Auto Scaling Group)
- **Load Balancing:** AWS Application Load Balancer
- **Database:** AWS RDS MySQL
- **Networking:** AWS VPC, Subnets, NAT Gateway, Internet Gateway
- **Monitoring:** AWS CloudWatch, SNS
- **AI Integration:** AWS Lambda, EventBridge, OpenAI API
- **Storage:** AWS S3, DynamoDB

---

## What's Implemented vs Planned

### ✅ Implemented
- Multi-AZ VPC networking
- ALB + Auto Scaling Group + RDS
- CloudWatch alarms with SNS notifications
- AI log summarization (Lambda + OpenAI + S3 + DynamoDB)
- EventBridge alarm routing
- Security groups (least privilege)
- Complete infrastructure as code

### 📋 Planned
- HTTPS with ACM certificate
- WAF rules
- Secrets Manager integration
- Multi-region DR
- Enhanced dashboards
- Auto-scaling policies

---

**Author:** Josh Holman  
**Date:** February 2, 2026  
**Region:** us-east-1  
**Terraform Version:** 1.x
