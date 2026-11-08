# RSVP Cloud Platform — Architecture

This documents the three-stage engineering design introduced in the [README](../README.md).

## Application and boundaries

A small Python application provides health/version endpoints and MySQL read/write behavior. Projects 1 and 2 demonstrate different hosting and delivery models for the same application contract. They do not need to run simultaneously or share a live database.

## Stage 1 — Private EC2 and RDS

```text
Internet → HTTPS/WAF → ALB → private EC2 (AZ A + AZ B)
                                   ↓
                         encrypted Multi-AZ RDS
```

The VPC isolates application and database resources. Security groups restrict traffic; CloudWatch and flow logs support troubleshooting. Backups and snapshots support recovery.

**Incident path:** CloudWatch alarm → EventBridge → Lambda → bounded log/metric evidence → validated AI or deterministic fallback → encrypted S3 and DynamoDB. AI is advisory and cannot change infrastructure.

**Live evidence:** Private targets in two AZs, HTTPS, WAF rejection, alarms, and a snapshot restore verified against a known record in **10m 02s**. Daily backup delivery, point-in-time recovery, and AZ failover are design capabilities, not all independently proven by that exercise.

## Stage 2 — ECS and controlled releases

```text
GitHub Actions → tests/scans → ECR immutable image
                                  ↓
                          private ECS Fargate
                                  ↓
                          HTTPS health checks
```

GitHub Actions assumes short-lived AWS credentials through OIDC. Terraform owns the infrastructure and task-definition baseline; the deployment workflow owns application releases.

Two recovery paths are distinct: the **ECS circuit breaker** rolls back unhealthy task deployments, while **workflow rollback** handles failed release checks. The live exercise proved the native ECS rollback in **13m 47s**, not every workflow recovery path. Scaling configuration does not by itself prove load-driven scaling.

## Stage 3 — Governance and operations

```text
AWS Organizations
 ├─ Management: policies and cost oversight
 ├─ Security: findings and incident analysis
 ├─ Log Archive: audit evidence
 └─ Workload accounts: applications and reporting
```

Terraform models SCPs, Identity Center, CloudTrail, security aggregation, dashboards, and cost analysis. Offline tests validate configuration contracts and handler behavior. **Live OU enforcement, cross-account integration, and identity flows remain unverified.**

## Operating principles

- **Isolation:** RSVP Society production resources and DNS are out of scope for portfolio changes.
- **Ownership:** Review backend identity, Terraform plans, and resource ownership before any apply.
- **Recovery:** Preserve encrypted snapshots and their KMS keys; measure recovery during controlled exercises.
- **Cost:** Time-box paid environments and track retained recovery assets.
- **AI:** Validate outputs and keep infrastructure changes under human control.

## Evidence and procedures

[Project 1 live report](PROJECT-1-LIVE-2026-11-08.md) · [Project 2 live report](PROJECT-2-LIVE-2026-11-08.md) · [Operations and validation matrix](OPERATIONS.md#validation-and-recovery)
