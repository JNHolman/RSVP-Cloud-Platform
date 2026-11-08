# RSVP Cloud Platform

**An AWS engineering portfolio built from a real business decision.**

I originally designed traditional AWS infrastructure for [RSVP Society](https://github.com/JNHolman/rsvp-society), my event-management platform. It worked as an architecture, but it was too expensive for a business with traffic concentrated around invitations and events.

I moved RSVP Society to event-driven services—Lambda, API Gateway, DynamoDB, and EventBridge—and kept the original enterprise infrastructure work as a separate engineering project.

## Three stages

| Stage | Engineering focus | What it demonstrates |
| --- | --- | --- |
| **1. Foundation** | Private EC2, ALB/WAF, Multi-AZ RDS, monitoring, backups | Secure networking, availability, recovery, incident analysis |
| **2. Delivery** | ECS Fargate, ECR, GitHub OIDC, CI/CD | Immutable releases, private containers, health checks, rollback |
| **3. Governance** | Organizations, SCPs, identity, audit logging, security and cost analysis | Multi-account operating controls, tested offline |

The first two stages use the same small application and data contract. The third models enterprise controls without claiming a live six-account deployment.

## What I verified

- **Project 1:** Two private application targets across two Availability Zones, HTTPS, WAF blocking, monitoring, and an encrypted RDS snapshot restore. **Measured restore: 10m 02s.**
- **Project 2:** GitHub OIDC delivery to private ECS tasks and a deliberately failed release recovered by the ECS circuit breaker. **Measured rollback: 13m 47s.**
- **Project 3:** Terraform policy and application behavior validated offline. Organization-wide enforcement has not been tested live.

These are dated test results, not claims that every integration is currently deployed. See the [Project 1](docs/PROJECT-1-LIVE-2026-11-08.md) and [Project 2](docs/PROJECT-2-LIVE-2026-11-08.md) reports.

## Engineering decisions

**Business fit:** RSVP Society uses lighter event-driven infrastructure; this portfolio explores controls justified by larger workloads.

**Operational safety:** Terraform owns infrastructure; GitHub Actions owns application releases. Environments are temporary, and the lab must not affect Society production.

**Recovery over configuration:** I measure restoration and rollback instead of assuming that configured safeguards work.

**Security boundaries:** AWS Config aggregation covers accounts only **where Config recording is enabled**. **RDS recovery points inherit the database encryption key**; recovery depends on retaining that key and access. **Project 1 recovery KMS keys have intentional Terraform destruction guards**.

## Documentation

[Architecture](docs/ARCHITECTURE.md) · [Operations, validation, costs, and cleanup](docs/OPERATIONS.md)

**Josh Holman** — Network / Cloud Infrastructure Engineer
