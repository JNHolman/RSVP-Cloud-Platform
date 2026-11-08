# Architecture: one platform, three stages

RSVP Cloud Platform started with a straightforward problem: **how do you put an application on AWS, release changes safely, and support it when something goes wrong?**

The three projects are stages of that engineering journey:

1. **Build:** network, servers, database, monitoring, and backup.
2. **Modernize:** containers, automated deployments, scaling, and rollback.
3. **Operate:** access controls, security findings, cost analysis, and incident response.

The stages share an intended application and operational story. **They are not yet one integrated live deployment.** Project 1 currently serves an Apache demo page; Project 2 serves a different Flask demo app. Project 3 is a multi-account reference design tested offline. Integrating a shared application is a planned correction, not a completed claim.

## 1. Build a secure foundation

**What problem does this solve?** A web service needs to be reachable by customers without exposing its servers or database directly.

```text
Visitor
   |
   v
HTTPS + AWS WAF (web firewall)
   |
   v
Application Load Balancer (public entry point)
   |
   +---------------------------+
   |                           |
   v                           v
Private EC2 (AZ 1)         Private EC2 (AZ 2)
   |
   | intended application data path; not yet used by demo page
   v
Private encrypted RDS MySQL (Multi-AZ)

CloudWatch monitors health and errors.
RDS snapshots and AWS Backup are configured for recovery.
```

The VPC separates public entry points from private workloads. Security groups permit only necessary connections. The application servers have no public IP addresses, and the database accepts connections from the application security group rather than the internet.

The deployment uses two Availability Zones so losing a single zone does not automatically mean losing every web server. Multi-AZ RDS provides a database availability configuration, but **a failover exercise has not been measured**.

**Actual proof:** Two private EC2 instances served HTTPS from different AZs; the WAF blocked a synthetic request; a CloudWatch alarm changed state; a known database record survived a snapshot restore. The timed restore took **10 minutes 2 seconds** from request to verified read.

**Limit:** The EC2 landing page currently doesn't query the database. The snapshot restore proves database recovery, not an application-level transaction or complete service recovery time.

[Project 1 live test](PROJECT-1-LIVE-2026-11-08.md)

## 2. Modernize the application delivery

**What problem does this solve?** Teams need to ship new versions without relying on manual steps, permanent deployment keys, or an unsafe rollback process.

```text
Code change
   |
   v
GitHub Actions → application tests → container security scan
   |
   v
ECR (versioned container image)
   |
   v
ECS Fargate → private tasks across two AZs
   ^
   |
HTTPS + WAF + Load Balancer ← Visitor

Bad task revision → ECS circuit breaker → previous healthy revision
```

The container is a small Python/Flask service. GitHub Actions uses AWS OIDC to request short-lived AWS credentials. The release image uses an immutable Git commit identifier. ECS runs private tasks behind an HTTPS load balancer.

Terraform defines the ECS infrastructure baseline. GitHub Actions owns application updates. This separation prevents a Terraform-only change from silently restoring an older application release.

**Actual proof:** GitHub delivered a versioned image to a healthy two-AZ service. A deliberately broken ECS revision triggered automatic recovery to the last healthy version in **13 minutes 47 seconds**.

**Limits:** The GitHub workflow has an additional rollback step that has not been exercised through its own failure path. CPU/memory autoscaling is configured but has not been shown responding to load. The application has not yet been unified with Project 1's EC2 workload or connected to its RDS database.

[Project 2 live test](PROJECT-2-LIVE-2026-11-08.md)

## 3. Add enterprise operations and governance

**What problem does this solve?** As applications and teams grow, security records, administrator privileges, and spending should not depend on one shared account or one person's access.

```text
AWS Organizations (proposed multi-account design)
|
+-- Management: account setup, policies, cost analysis
+-- Security: central findings and incident analysis
+-- Log Archive: protected audit records
+-- Workloads: applications and approved read-only reporting
```

The design uses organizational guardrails (Service Control Policies), IAM Identity Center for permissions, AWS CloudTrail for audit records, and GuardDuty/Security Hub for security findings. A restricted operations API is designed to let approved users view selected reports without broad administrative access.

Security and FinOps handlers can summarize findings and cost data. Model output is checked against expected fields. Sensitive identifiers are limited or redacted before analysis. A fallback report remains available when the model fails.

**Actual proof:** Terraform tests generate and check the policies, and Python tests exercise local event processing, authorization-related configuration, redaction, and fallback behavior.

**Limit:** There is no demonstrated live six-account deployment. Real policy enforcement, cross-account role access, centralized delivery, and Identity Center sign-in are unverified.

## How the stages fit together

The intended progression is **one application moving from traditional hosting to a container deployment, with stronger operational controls around it**.

Today, the code shows those capabilities in separate reference implementations. That decision made individual tests and teardown safer in a shared AWS account, but it left an important integration gap.

The next engineering correction is to use a consistent small application and database contract in Projects 1 and 2, **without forcing them to share Terraform state or keeping both deployments running at once**. Project 3 stays an offline-validated enterprise expansion unless a real integration environment is approved.

Do not describe that future integration as complete until the application path has actually been tested.

## Why these choices matter

| Choice | Benefit | Cost or limitation |
| --- | --- | --- |
| Private compute and database | Limits direct public exposure | Network routing and NAT cost more |
| Two Availability Zones | Less reliance on one location | More resources to pay for |
| Terraform plus GitHub Actions | Repeatable infrastructure and safer application releases | Two clearly defined ownership boundaries |
| OIDC instead of stored AWS deployment keys | Short-lived authentication | GitHub Environment restrictions become important |
| Human-approved AI analysis | Faster investigation without autonomous changes | The operator remains responsible |
| Separate governance accounts | Reduced organizational blast radius | More complexity; validated offline here |

## AI and incident response

Project 1 contains the intended alarm → EventBridge → Lambda → analysis → encrypted evidence path. Direct Lambda fallback and a separate local model call were tested. **The complete alarm-triggered sequence has not been verified.** The unhealthy-target alarm used in the live demo also was not included in the AI event-rule alarm list at that point.

Project 3 includes separate handlers for security finding analysis and cost analysis. Their offline tests cover failure handling, redaction, and bounded outputs. These are not evidence of production incident automation.

AI assists diagnosis; it is not authorized to change networks, databases, deployments, or account policies.

## Source and evidence

| Question | Go to |
| --- | --- |
| What passed in AWS, and what's unfinished? | [Tests and evidence](PORTFOLIO-VALIDATION.md) |
| How do I reproduce a test safely? | [Deployment and validation](DEPLOYMENT.md) |
| What happened during the EC2/RDS test? | [Project 1 live report](PROJECT-1-LIVE-2026-11-08.md) |
| What happened during the ECS rollback test? | [Project 2 live report](PROJECT-2-LIVE-2026-11-08.md) |
| Where is the implementation? | [Infrastructure code](../infrastructure/) and [GitHub workflows](../.github/workflows/) |
