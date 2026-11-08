# How RSVP Cloud Platform works

This is the technical explanation of the story in the [main README](../README.md).

I started with infrastructure that was too expensive and complicated for RSVP Society's actual workload. RSVP Society moved to a lighter, event-driven design. RSVP Cloud Platform kept the more extensive AWS design so I could work through the engineering questions that come with a larger environment.

The result is **one application moving through three stages**: build it, modernize how it runs, then develop the controls needed to operate it at scale.

These stages are an engineering progression. They don't require three permanently running environments.

## First, the application

The application is deliberately small. I don't need a second event-management product to prove the infrastructure works.

The same Python application and data behavior are used in the EC2 and ECS stages. It exposes a health check, identifies the running version, and reads and writes a small amount of test data in MySQL.

That last part matters. A web page that displays successfully doesn't prove the database connection works. A real application request does.

I can run the application locally, test it without AWS, and deploy it to either hosting model. Each live environment keeps clearly defined Terraform ownership and can be cleaned up independently. There is no requirement for both hosting models to share a live database or run simultaneously.

## Stage 1 — Secure application infrastructure

```text
User
 |
 v
HTTPS + WAF (web firewall)
 |
 v
Application Load Balancer
 |
 +---------------------+
 |                     |
 v                     v
Private EC2          Private EC2
Zone A               Zone B
 |                     |
 +----------+----------+
            |
            v
  Private, encrypted MySQL
  (Multi-AZ Amazon RDS)
```

**What this solves:** Users can reach the application without exposing the machines and database that run it.

The VPC separates internet-facing services from internal workloads. Security groups limit which components may communicate. The database remains private, while redundant application servers and a Multi-AZ database reduce dependence on one Availability Zone.

CloudWatch collects metrics and logs. The web firewall (AWS WAF) filters unwanted requests. Backups and snapshots provide a recovery path.

I also built an incident analysis path:

```text
CloudWatch alarm
       |
       v
   EventBridge
       |
       v
      Lambda
       |
       +--> Collect bounded evidence from logs and metrics
       +--> Analyze it and check the result
       +--> Save the report in encrypted S3 and DynamoDB
       +--> Notify an operator
```

AI is useful for organizing the evidence and suggesting what to investigate next. It doesn't get permission to terminate servers, change a firewall, or modify a database. If the model or API isn't available, a rule-based fallback still returns useful incident information.

**Recovery:** AWS Backup, RDS point-in-time recovery, and controlled Multi-AZ failover are part of the recovery procedures. Each recovery exercise uses disposable resources, a known test record, and recorded timing so the result can be evaluated rather than assumed.

## Stage 2 — Modernize application hosting and releases

The application is now packaged into a Docker image and run on ECS Fargate rather than installed directly on EC2 servers.

```text
Code change
    |
    v
GitHub Actions
    |
    +--> Test the application
    +--> Check dependencies and scan the container
    +--> Build a version tied to the Git commit
    |
    v
Amazon ECR (container registry)
    |
    v
ECS Fargate (private tasks in two zones)
    |
    v
Health check and release verification
    |
    +--> Healthy: keep the new release
    |
    +--> Failed: restore the last working release
```

The application and its data contract stay consistent; the hosting and delivery model change.

GitHub Actions obtains short-lived AWS credentials through OIDC instead of storing a permanent deployment key. Amazon ECR holds versioned images. ECS runs the private application tasks behind HTTPS and uses CPU/memory policies to adjust capacity as demand changes.

There are two separate recovery mechanisms, and they solve slightly different problems:

- **ECS deployment circuit breaker:** Restores the last working task revision if the new tasks cannot become healthy.
- **GitHub workflow rollback:** Restores the previous working release when a release fails its deployment checks.

The first was demonstrated in an earlier live exercise with a measured **13-minute, 47-second** recovery. The second is tested as an independent workflow path, rather than being credited to the ECS circuit breaker.

Terraform owns the baseline infrastructure. GitHub Actions owns the application release. That prevents an ordinary infrastructure plan from unexpectedly rolling the app back to an older version.

**A cost decision:** I don't keep the EC2 and ECS versions running indefinitely. They're alternative stages of the same application's evolution, not two required production systems.

## Stage 3 — Security, governance, and operations

At a larger company, the people running applications shouldn't necessarily control the security records or the organization's account policies.

The enterprise design separates those responsibilities:

```text
AWS Organizations
 |
 +-- Management: account rules and cost oversight
 |
 +-- Security: findings and incident analysis
 |
 +-- Log Archive: protected audit records
 |
 +-- Workload accounts: applications and approved reporting
```

The Terraform design covers AWS Organizations, Service Control Policies, centralized CloudTrail logging, IAM Identity Center, security findings, and a limited operations dashboard.

The security and cost analysis handlers help an operator answer two familiar questions: **What needs attention?** and **Where is the money going?**

The design is modeled and tested locally. That lets me validate policy generation, data handling, permission contracts, and AI fallback behavior without maintaining a fleet of AWS accounts.

These are enterprise operating patterns, not a claim that RSVP Society itself needs them.

## How I keep the system safe to work on

RSVP Society production and RSVP Cloud Platform have separate responsibilities. A lab change must not touch the event business.

- **State ownership:** Each Terraform root has an explicit backend and owner. No other stack should start managing the same live resource.
- **Change approval:** Terraform plans are reviewed. Infrastructure isn't automatically applied just because code changed.
- **Account and DNS boundaries:** Dev resources and delegated DNS records stay separate from Society production.
- **Security controls:** Workloads stay private, deployments use short-lived credentials, and AI output is checked before it is saved.
- **Recovery protection:** Snapshots and the encryption keys required to restore them are preserved deliberately.
- **Cost controls:** Paid test workloads are time-boxed and removed when the exercise is complete. Retained resources are tracked because cleanup does not always mean a zero-dollar bill.

## Trade-offs I would explain in an interview

| Decision | Why I made it | What I accepted |
| --- | --- | --- |
| Move RSVP Society to event-driven AWS services | The business has uneven traffic and needs manageable operating costs | More attention to event ordering, state, and retry handling |
| Use EC2 and RDS for the foundation project | Learn and demonstrate the controls needed for a traditional hosted application | Always-on compute, networking, and database costs |
| Move the same app to ECS | Practice safer releases, scaling, and recovery | More deployment and container configuration |
| Use Terraform and GitHub Actions separately | Avoid confusing infrastructure changes with application releases | Clear ownership is essential |
| Design multi-account controls but test locally | Demonstrate the architecture without paying for unnecessary accounts | Live organization-wide behavior requires its own enterprise test environment |
| Keep AI advisory | Help with investigations without giving a model control of AWS | An operator still makes the decision |

## What the evidence proves

The [Project 1 live report](PROJECT-1-LIVE-2026-11-08.md) records private servers in two zones, working HTTPS, a WAF block, monitoring, and a database snapshot restore that took **10 minutes and 2 seconds** from restore request to verified record.

The [Project 2 live report](PROJECT-2-LIVE-2026-11-08.md) records GitHub-driven delivery, private container placement, a failed release, and ECS recovery in **13 minutes and 47 seconds**.

Those reports are dated snapshots of earlier exercises. They aren't rewritten to make later engineering changes appear to have happened during the original tests. Integration tests, workflow checks, and additional recovery exercises belong with their own code and evidence.

For commands and safety requirements, use the [deployment guide](DEPLOYMENT.md). For the evidence index, see [testing and validation](PORTFOLIO-VALIDATION.md).
