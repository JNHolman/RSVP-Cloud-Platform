# Part 1 — Cloud Foundation

**The first problem was to build a traditional AWS application environment that I could secure, troubleshoot, and recover.**

I designed a public HTTPS entry point with the application and database in private networks. The VPC spans two Availability Zones; each has its own NAT gateway for private outbound traffic, so one AZ's egress path does not depend on the other. The EC2 application tier is managed by an Auto Scaling Group behind the load balancer.

```text
Internet → HTTPS / WAF / ALB
                     |
               private EC2 targets (AZ A + AZ B)
                     |
               intended private RDS connection
```

The EC2 demo page did not itself query RDS in the recorded exercise. The application and database paths were validated separately.

## How the design works

**Keep the network boundaries explicit.** Security-group references restrict the ALB-to-EC2 and application-to-database traffic paths. The default VPC security group is locked down so workloads need deliberately assigned rules. The public subnets host the entry and egress infrastructure; application instances and RDS do not need public IP addresses.

[Inspect VPC, routes and security groups](terraform/vpc.tf) · [Load balancer](terraform/alb.tf)

**Collect evidence before troubleshooting.** CloudWatch tracks unhealthy targets and application/infrastructure metrics; VPC Flow Logs and application logs show what traffic reached the environment. I also implemented an EventBridge/Lambda incident-analysis path to collect bounded diagnostic evidence and store an advisory result in encrypted S3 and DynamoDB. The handler has a deterministic fallback and cannot change infrastructure.

[Monitoring and alarms](terraform/monitoring.tf) · [Incident-analysis handler](terraform/ai_log_summarizer.py)

**Treat recovery as a separate test.** RDS uses private networking, storage encryption, managed credentials, and backup configuration. I retained the database encryption key using a Terraform destruction guard: a snapshot is useless if its key is deleted. For the live test, I deliberately restored a native snapshot to a separate database instead of assuming the configuration was sufficient.

[RDS configuration](terraform/rds.tf) · [Backup configuration](terraform/backup.tf)

## What happened in the AWS exercise

On November 8, 2026, two instances were healthy in different AZs and had no public IP addresses. An HTTPS check succeeded, WAF rejected a harmless test request, VPC/application logs arrived, and the unhealthy-target alarm moved from ALARM back to OK.

The database recovery test wrote a known marker, took a snapshot, restored a private RDS instance, and read the marker back over TLS. **Restore request to verified read: 10 minutes 2 seconds.**

The incident-analysis Lambda exposed a KMS permission problem during direct testing. I narrowed the DynamoDB decrypt permission to the relevant key and encryption context, then verified that the fallback result was stored. A separate local handler test exercised an AI-generated result.

**Not proven in this exercise:** an end-to-end page-to-RDS query, automatic alarm-to-Lambda delivery, AWS Backup recovery, point-in-time recovery, or Multi-AZ failover. The dated evidence distinguishes these from the tested paths.

[Original observations and recovery timeline](evidence/2026-11-08.md) · [Recorded results](evidence/observations.json)

The point of this part is the relationship between traffic, visibility, and recovery—not a catalogue of AWS services. It set the expectations I carried into container delivery.

[Platform overview](../README.md) · [Part 2: ECS & CI/CD](../project-2-ecs-cicd/README.md)
