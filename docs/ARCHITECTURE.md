# How RSVP Cloud Platform is built

The simple idea: **build the infrastructure, deliver changes safely, and know what to do when something fails.**

This repository has three projects. They share engineering principles, but they are **not one application running through every service in the diagram**.

| Project | What it demonstrates | What it does not claim |
| --- | --- | --- |
| **1. Cloud foundation** | Secure network design, private servers, encrypted database, monitoring and recovery | A complete business application connected to its database |
| **2. Application delivery** | Private containers, automated releases, health checks and rollback | A live production service or a database-backed application |
| **3. Governance and operations** | How accounts, access, logs, security findings and costs would be managed at scale | A deployed six-account organization |

## Project 1: Keep the application private and recoverable

```text
Visitor → HTTPS + WAF → Load balancer → Private EC2 servers
                                           │
                                     Application network
                                           │
                                     Private RDS database

CloudWatch → alarms → notifications
                     └→ EventBridge → AI incident analysis (end-to-end path not yet verified)
```

The load balancer accepts public requests. The servers and database do not have public addresses. Security groups limit which components can talk to each other. Two Availability Zones reduce dependence on one location.

The EC2 servers currently serve an Apache demonstration page and a health check. **That page does not query RDS.** The database was verified independently through a controlled backup-and-restore exercise. This proves the infrastructure and recovery path, not an integrated application transaction.

**If something breaks:** CloudWatch records signals and can alert an operator. The AI handler can analyze bounded alarm and log evidence, but automatic alarm-to-handler delivery has not yet been proven. AI does not make infrastructure changes.

**Recovery evidence:** A synthetic database record survived an encrypted snapshot restore. The request-to-verified-read time was **10 minutes 2 seconds**. That is a measured database restore, not a complete application recovery time.

[Project 1 live evidence](PROJECT-1-LIVE-2026-11-08.md)

## Project 2: Make application releases safer

```text
Developer → GitHub Actions → tests + image scan → immutable image in ECR
                                                      │
                                                      ▼
                                  Private ECS Fargate tasks in two AZs
                                                      ▲
Visitor → HTTPS + WAF → Load balancer ────────────────┘

Unhealthy new release → ECS deployment circuit breaker → last healthy release
```

GitHub Actions uses short-lived AWS credentials, not a saved deployment access key. Each release is tied to a Git commit so it can be identified later. ECS runs the container without giving it a public IP.

Terraform establishes the service configuration. GitHub Actions changes the application version. Keeping those responsibilities separate prevents an infrastructure update from accidentally undoing an application release.

**If a release fails:** ECS can restore the previous working task definition. This was demonstrated in AWS: a deliberately broken revision recovered in **13 minutes 47 seconds**. The GitHub workflow also contains its own rollback step, but that particular failure path has not been tested live.

CPU- and memory-based scaling policies exist. A load-driven scale-out and scale-in exercise has not been recorded.

[Project 2 live evidence](PROJECT-2-LIVE-2026-11-08.md)

## Project 3: Separate the accounts and responsibilities

A growing organization should not keep every workload, administrator and security record under the same permissions.

```text
AWS Organizations
├── Management: organization rules, account setup and cost analysis
├── Security: security findings and incident triage
├── Log Archive: centralized audit records
└── Workload accounts: applications and approved read-only reporting
```

The design uses Service Control Policies (organization-wide guardrails), Identity Center for access, and separate roles for reading security and cost reports. The AI tools summarize security findings and spending data; they cannot automatically remediate infrastructure.

**Evidence boundary:** Policy generation and application logic passed offline tests. Actual cross-account permissions, sign-in, delegated administration and organization-wide log delivery have **not** been tested in a deployed enterprise environment.

## The decisions that matter

| Choice | Why | Trade-off |
| --- | --- | --- |
| Private workloads | Reduce direct exposure to the internet | More network components and cost |
| Multiple Availability Zones | Avoid a single-zone dependency | Higher running cost |
| Terraform for infrastructure, GitHub for releases | Repeatable infrastructure without reverting application versions | Two workflows to understand and operate |
| Short-lived GitHub credentials | No permanent AWS deployment key in GitHub | Requires properly protected GitHub environments |
| AI as an adviser | Faster interpretation of incidents without unsafe automatic changes | An operator still makes decisions |
| Separate governance accounts | Limit the damage from a compromised workload | More accounts and operational overhead |

## Want to see the technical proof?

The [validation record](PORTFOLIO-VALIDATION.md) separates **live-tested**, **offline-tested** and **not-yet-tested** functionality. The [deployment guide](DEPLOYMENT.md) retains the commands, prerequisites and safety rules for a technical reviewer.

The point of this platform is not the number of AWS services. It is whether the design solves a problem, behaves correctly under failure, and can be explained and supported.
