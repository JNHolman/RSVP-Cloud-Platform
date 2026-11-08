# RSVP Cloud Platform

**Building, modernizing, and operating an application on AWS — with security, automation, and recovery built into the work.**

Imagine a company putting an application in the cloud. Getting the website online is only the beginning. It also needs to protect customer data, release updates safely, detect problems, recover from failures, and keep costs under control.

That's the engineering problem I wanted to work through.

RSVP Cloud Platform follows that journey in three stages:

| Stage | The question I wanted to answer | What I built |
| --- | --- | --- |
| **1. Build it** | How do I host an application securely and recover its data? | A private AWS network with EC2 servers, a load balancer, an encrypted database, monitoring, and backups |
| **2. Modernize it** | How do I release updates without breaking the service? | A containerized application with automated tests, deployments, health checks, scaling rules, and rollback |
| **3. Operate it** | How do I manage security, access, incidents, and spending as the environment grows? | A multi-account governance design with automated security and cost analysis, tested locally |

**This is one engineering journey, not three unrelated AWS service lists.** The code currently uses separate demonstration workloads for the EC2 and container stages; making them one shared application is the remaining integration work. The six-account governance design is deliberately not deployed.

## What I've demonstrated

These aren't just diagrams or planned features. In isolated AWS test environments, I:

- **Protected application traffic.** Served HTTPS through a load balancer and web firewall, while keeping compute instances and containers off the public internet.
- **Tested real recovery.** Restored an encrypted database snapshot, connected to the restored database, and confirmed the original test record was there. The restore request to verified read took **10 minutes 2 seconds**.
- **Deployed updates through automation.** Used GitHub Actions and short-lived AWS credentials to test, build, scan, and release a container to ECS.
- **Broke a release on purpose.** Watched AWS ECS automatically restore the previous healthy version in **13 minutes 47 seconds**.
- **Tested incident analysis.** Ran the AI handler against test alarm data, verified its safe fallback, and separately checked a live model response. The complete automatic alarm-to-AI path still needs a live test.

I also wrote offline tests for the governance and security design. **Offline validation is not the same as running a six-account AWS environment.**

[See exactly what passed, what failed, and what remains open](docs/PORTFOLIO-VALIDATION.md).

## How the platform grows

### 1 — Start with a secure foundation

The first stage uses a traditional AWS design: a public entry point, private servers in two Availability Zones, a private MySQL database, monitoring, and backups.

I wanted to answer practical questions: Can someone reach the servers directly? Will traffic reach a healthy server if one fails? Can I restore the database and prove the data survived?

**What is working:** The networking, HTTPS, firewall, monitoring signals, and database restore were tested in AWS.

**What remains:** The current EC2 demo page does not yet make an application-level query to RDS. Additional backup and failover scenarios also need live testing.

### 2 — Make releases safer

The next stage uses a Python application running in containers on ECS Fargate. GitHub Actions tests the application, scans its image, and deploys a version that can be traced back to the source code.

Why? Because a deployment is only successful if the new version actually works — and the team needs a way back when it doesn't.

**What is working:** A GitHub-driven release, two healthy private containers across two Availability Zones, and an ECS-managed rollback were demonstrated.

**What remains:** The GitHub workflow's separate rollback path and load-driven autoscaling need live tests. The newer container image also has two reported high-severity findings that need to be resolved or assessed.

### 3 — Prepare to operate at a larger scale

The final stage asks how the same operating approach would work across teams and AWS accounts.

The design separates applications, security administration, and audit logs. It includes account-level guardrails, restricted access, security-event analysis, and cost reporting. AI helps interpret evidence; it does **not** make changes to infrastructure on its own.

**What is working:** The Terraform policies and application logic have automated offline tests.

**What remains:** Cross-account access, AWS security-service enrollment, centralized log delivery, and real user sign-in have not been validated in a deployed multi-account environment.

## Why I built it

This project started as a proposal to move [RSVP Society](https://github.com/JNHolman/rsvp-society), my private-event platform, onto AWS.

The original three-tier infrastructure was more expensive and complex than that business needed. Instead of forcing the business to use it, I separated the projects. RSVP Society follows its actual operating needs; RSVP Cloud Platform became the place where I could explore larger-scale cloud engineering.

My background is enterprise network engineering. During an outage, the most useful questions are usually straightforward: **What's failing? What changed? Who is affected? How do we prove the cause and restore service?**

I wanted to apply that same thinking to AWS, Terraform, containers, deployment automation, security, and AI-assisted operations.

## A few decisions that matter

| Decision | Why I chose it | Trade-off |
| --- | --- | --- |
| Keep application servers private | Limit what is exposed directly to the internet | More network components |
| Run workloads across two Availability Zones | Reduce dependence on a single location | Higher running cost |
| Use GitHub Actions for application releases | Make changes repeatable and recoverable | Release permissions must be protected |
| Use Terraform for infrastructure | Make configuration reviewable and reproducible | Infrastructure changes still need careful approval |
| Keep AI advisory | Help engineers interpret incidents without giving a model control of production | People still make the changes |
| Test briefly, then tear down | Demonstrate real AWS behavior without a permanent enterprise-sized bill | Some tests must be scheduled separately |

**This repository is an engineering portfolio, not a claim that all three stages are running together in production.** Projects 1 and 2 were deployed for controlled tests and their temporary workloads were removed. Retained backups, encryption keys, logs, and images may still incur charges. RSVP Society production is separate and must not be affected by this work.

## Explore the work

| Start here | What you'll find |
| --- | --- |
| [Architecture](docs/ARCHITECTURE.md) | How the three stages fit together, their AWS components, and the design choices |
| [Tests and evidence](docs/PORTFOLIO-VALIDATION.md) | Live results, outstanding tests, and the limits of each claim |
| [Project 1 live exercise](docs/PROJECT-1-LIVE-2026-11-08.md) | Private networking, HTTPS, alarms, and the timed database restore |
| [Project 2 live exercise](docs/PROJECT-2-LIVE-2026-11-08.md) | Automated deployment, failed release, ECS rollback, and image scan |
| [Deployment and testing guide](docs/DEPLOYMENT.md) | Technical prerequisites, safe execution procedures, and cleanup |

The implementation is under [`infrastructure/`](infrastructure/), the workflows are under [`.github/workflows/`](.github/workflows/), and automated tests are under [`tests/`](tests/).

---

**Josh Holman** · Network / Cloud Infrastructure Engineer
