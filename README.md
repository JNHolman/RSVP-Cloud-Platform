# RSVP Cloud Platform

**An AWS engineering portfolio built around a real application: RSVP Society.** The work covers private networking, automated incident investigation, container delivery and recovery, and AI-assisted security governance.

[RSVP Society](https://github.com/JNHolman/rsvp-society) is a private-event operations platform. Hosts approve members, release invitations in waves, manage RSVPs and guests through text conversations with Jade, and use check-in records to track who attended. Activity arrives in bursts around events rather than at a steady rate.

I originally built a more traditional AWS environment for the application: private servers behind a load balancer and a highly available relational database. That architecture was useful for learning how the whole request path behaves, but it was expensive to keep running between events. The business application subsequently moved toward event-driven services. **I kept the original design as a separate, disposable engineering lab—not as the current Society production architecture.**

I used that lab to answer three practical questions: **Can I establish why a service failed? Can I reject and recover a bad release? Can I keep security decisions and audit evidence outside the control of the workload team?**

## Three projects, one engineering story

### [1. Cloud Foundation — private infrastructure and incident investigation](project-1-cloud-foundation/README.md)

Built a protected HTTPS path through AWS WAF and an application load balancer to private EC2 instances and encrypted Multi-AZ RDS. Added CloudWatch, EventBridge and Python Lambda to collect incident evidence, request AI-assisted analysis, validate the response and preserve a report for an operator.

**The engineering question:** When a request fails, what evidence separates a network problem, an unhealthy application and a database problem—and can that evidence be collected without an engineer gathering it by hand?

### [2. ECS Delivery — controlled releases and independent recovery](project-2-ecs-cicd/README.md)

Deployed the same read-only application on private ECS Fargate tasks in a separate VPC, connected to the original database over VPC peering. GitHub Actions built and scanned immutable images, used OIDC for temporary AWS access, checked the serving application version and restored the previous release when verification failed.

**The engineering question:** What if infrastructure reports healthy but customers are receiving the wrong software?

### [3. Cloud Governance — account boundaries and AI security guardrails](project-3-cloud-governance/README.md)

Designed a six-account AWS organization that separates administration, security, audit records, shared services and workloads. Built Terraform for access policies, audit infrastructure, security operations and cost reporting. Exercised one AI security decision in a single AWS account: a model proposed P3 for a critical sample, but deterministic policy enforced P1.

**The engineering question:** How do you let teams operate their systems without letting them weaken the controls or rewrite the evidence used to investigate them?

## See the controls in action

![Animated reconstruction of recorded Cloud Foundation, ECS release recovery and governance exercises](shared/platform-exercises.gif)

*25-second reconstruction of three recorded exercises, not live console footage.* [Incident report](project-1-cloud-foundation/README.md#ai-assisted-investigation) · [Release rollback](project-2-ecs-cicd/README.md#two-independent-recovery-controls) · [Security priority decision](project-3-cloud-governance/README.md#the-live-security-exercise)

## How the architecture fits together

The foundation path serves HTTPS through an ALB and WAF to **private EC2** and **private RDS**. The delivery path serves HTTPS to **private Fargate tasks** in another VPC; peering, return routes, security-group rules and IAM database authentication allow those tasks to read the **same RDS records**. A successful HTTP health check alone does not prove that the application can reach its data.

The automation is deliberately separate from the application:

- **Incident investigation:** A CloudWatch metric alarm changes state; EventBridge invokes Lambda; Lambda collects bounded, redacted log evidence and requests AI analysis. Validated reports go to encrypted storage, and SNS delivered the reference to an encrypted test queue. AI provides a diagnosis to check, not an automatic repair.
- **Release verification:** ECS checks task stability. GitHub Actions independently verifies the version served over HTTPS and can restore the last known release. The newer database-aware smoke checks also require the expected reservation row, but those additions have only simulated workflow-test coverage.
- **Security triage:** A security-event handler uses AI to recommend priority, then enforces a deterministic severity floor before storing and notifying. The six-account separation is an enterprise design with offline validation; the live triage exercise ran in one account.

## What I verified

- **77 application log entries** were collected in an AI-assisted incident run after I deliberately set the development alarm to ALARM. The logs included real earlier 503 responses; the model suggested a *likely* backend connection problem rather than a proven root cause. [Investigation evidence](project-1-cloud-foundation/README.md#ai-assisted-investigation)
- **3m 23s** to reject a healthy-but-wrong release and verify that the previous version was serving again. A separate unhealthy-task exercise recovered through the ECS circuit breaker in **13m 47s**. [Delivery evidence](project-2-ecs-cicd/README.md#live-aws-results)
- **10m 02s** from an encrypted database snapshot restore request to a successful private TLS read of a known row. Point-in-time recovery, AWS Backup and Multi-AZ failover were exercised separately with different completion criteria. [Recovery evidence](project-1-cloud-foundation/README.md#database-recovery)
- **Two to three running ECS tasks** under a measured load exercise. Scale-in was not confirmed. [Capacity evidence](project-2-ecs-cicd/README.md#capacity-and-image-security)
- **P3 proposed, P1 enforced** for a labeled critical finding. DynamoDB retained both decisions; SNS delivered the alert to an encrypted SQS subscriber. [Security evidence](project-3-cloud-governance/README.md#the-live-security-exercise)

These are results from specific development exercises, **not service-level guarantees**.

## Engineering decisions that connect the projects

**Use evidence stronger than a green health check.** Project 1 tested the full path to a private database. Project 2 added release identity and data-read verification because a running container can still serve the wrong code or fail on a dependency.

**Keep AI useful without making it authoritative.** Incident analysis preserves raw evidence and low-confidence fallbacks. Governance stores the model's recommendation but uses explicit policy for the final priority. Both systems give an engineer an auditable starting point rather than an unreviewed change.

**Separate operational ownership.** Terraform established the infrastructure baseline; GitHub Actions owned application revisions. Foundation owned the database, while Delivery owned its peering routes and reader permissions. Governance extends that principle to separate accounts for workload operators, security investigators and audit history.

**Protect the actual business.** The lab used scoped names, state keys and a delegated `cloud.rsvpsociety.com` DNS zone. I reviewed changes to keep Society production resources out of scope, then retired the lab runtimes rather than leaving them running continuously.

## Implementation, validation and limits

Each project README links to its Terraform, Python, workflows and captured evidence. The main [CI workflow](.github/workflows/ci.yml) runs software and infrastructure checks; the [Checkov disposition](shared/checkov-review.md) explains advisory infrastructure findings rather than treating a green CI job as proof of zero risk.

Some boundaries matter: the newer database-aware rollback tests used simulated responses after the ECS/RDS lab was retired; governance policy logic and the six-account architecture were tested offline rather than enforced across live member accounts. The live notification exercises verified **SQS receipt**, not human email delivery. Project 2 also documents that the `prod` GitHub Environment lacked branch/tag restrictions and reviewer rules when inspected. The detailed results and limits are beside the relevant code in the project pages.

Retained snapshots, encryption keys and evidence storage may still incur costs; no reliable portfolio-only billing total was available. The retired runtime was not restarted for documentation.

**What this portfolio demonstrates:** I can design private application paths, automate evidence collection and release recovery, distinguish an observed result from an inference, and put explicit controls around both infrastructure changes and AI decisions.
