# Project 1 Deployment Evidence

**Deployment Date:** February 2, 2026  
**Status:** ✅ Successfully Deployed and Verified

---

## Infrastructure Overview

This folder contains evidence of a complete, working AWS infrastructure deployment for the RSVP Cloud Platform Project 1.

### Resources Deployed

| Resource Type | Resource ID/Name | Status |
|---------------|------------------|--------|
| VPC | `vpc-06b57ae331224b367` | ✅ Active |
| Public Subnets | `subnet-03d6d590c3dce9465`, `subnet-0d5865b3e54db3137` | ✅ Active |
| Private Subnets | `subnet-0f8559726ebd85b7c`, `subnet-091320986dc45743d` | ✅ Active |
| Application Load Balancer | `rsvp-dev-alb` | ✅ Active (2 healthy targets) |
| Auto Scaling Group | `rsvp-dev-asg` | ✅ Active (2 instances) |
| RDS MySQL Database | `rsvp-dev-db` | ✅ Available |
| Lambda Function | `rsvp-dev-ai-log-summarizer` | ✅ Active |
| S3 Bucket | `rsvp-dev-ai-logs` | ✅ Active (with summaries) |
| DynamoDB Table | `rsvp-dev-ai-log-summaries` | ✅ Active (with records) |
| CloudWatch Alarms | Multiple | ✅ Configured and firing |

---

## Live Endpoints

**Application URL:**  
http://rsvp-dev-alb-1273619337.us-east-1.elb.amazonaws.com/

**Health Check:**  
http://rsvp-dev-alb-1273619337.us-east-1.elb.amazonaws.com/health

---

## Screenshots

### Infrastructure Components

1. **`vpc-overview.png`** - VPC configuration showing CIDR blocks and availability zones
2. **`subnets-list.png`** - Public and private subnets across 2 AZs
3. **`alb-overview.png`** - Application Load Balancer configuration and listeners
4. **`target-group.png`** - Target group with 2 healthy EC2 instances
5. **`autoscaling-group.png`** - Auto Scaling Group with desired capacity of 2
6. **`rds-overview.png`** - RDS MySQL instance in Available state

### Application Components

7. **`project-ui.png`** - Live web application showing deployed page
8. **`lambda-function.png`** - AI log summarizer Lambda function
9. **`s3-bucket-overview.png`** - S3 bucket structure for AI summaries
10. **`s3-summary-object.png`** - Example AI-generated summary stored in S3
11. **`cloudwatch-alarms.png`** - CloudWatch alarms for monitoring

---

## Verification Results

### ✅ VPC & Networking
- VPC created with DNS support enabled
- 2 public subnets with internet gateway
- 2 private subnets (for compute and database)
- Route tables properly configured

### ✅ Compute Layer
- Application Load Balancer accepting HTTP traffic
- 2 EC2 instances running in private subnets
- Both targets healthy and passing health checks
- Auto Scaling Group maintaining desired capacity

### ✅ Database Layer
- RDS MySQL instance in available state
- Located in private subnets (not publicly accessible)
- Security group allowing access only from app instances

### ✅ AI Log Summarization
- Lambda function successfully deployed
- EventBridge rule routing CloudWatch alarms to Lambda
- S3 bucket storing AI-generated summaries
- DynamoDB table tracking summary metadata
- Real alarms fired and processed

### ✅ Security
- Security groups follow least-privilege principle
- ALB → Only from internet on port 80
- App instances → Only from ALB on port 80
- RDS → Only from app instances on port 3306
- All egress allowed for updates/API calls

---

## Architecture Highlights

**Multi-AZ Design:**
- Resources distributed across us-east-1a and us-east-1b
- Provides high availability and fault tolerance

**Network Segmentation:**
- Public subnets: Internet-facing resources (ALB)
- Private subnets: Application logic (EC2, RDS)
- No direct internet access to compute or database

**AI-Powered Monitoring:**
- CloudWatch alarms trigger EventBridge rules
- Lambda analyzes logs with OpenAI integration
- Structured summaries stored for incident response

---

## Cost Summary

**Estimated Monthly Cost:** ~$80-90 (us-east-1, dev sizing)

| Service | Monthly Cost |
|---------|--------------|
| VPC/Networking | Free |
| NAT Gateway | ~$32 |
| ALB | ~$16 |
| EC2 (t3.micro × 2) | ~$14 |
| RDS (db.t3.micro) | ~$15 |
| Lambda/S3/DynamoDB | ~$5 |

**Note:** Infrastructure can be torn down with `terraform destroy` when not in use.

---

## Technical Implementation

**Infrastructure as Code:**
- 100% Terraform managed
- 45 resources created in single apply
- Remote state management ready

**Deployment Pattern:**
- Deterministic and repeatable
- No manual console configuration
- Full audit trail via Terraform state

**Production Readiness:**
- Health checks configured
- Monitoring and alerting active
- Security groups properly scoped
- AI-enhanced operational intelligence

---

## Next Steps for Production

While this deployment is fully functional, production hardening would include:

- [ ] HTTPS termination with ACM certificate
- [ ] WAF rules for application protection
- [ ] Secrets Manager for sensitive data (RDS password, API keys)
- [ ] Multi-region failover
- [ ] Enhanced IAM roles (more specific resource ARNs)
- [ ] Auto-scaling policies based on metrics
- [ ] CloudWatch dashboard for monitoring
- [ ] Budget alerts and cost controls

---

**Evidence collected by:** Josh Holman  
**Deployment tool:** Terraform v1.x  
**AWS Region:** us-east-1  
**Date:** February 2, 2026
