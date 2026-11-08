# Tests and evidence: what worked, and what's still open

**The short version:** Project 1's network and database recovery were live-tested. Project 2's automated deployment and ECS recovery were live-tested. Project 3's enterprise governance was tested offline. The shared application and some end-to-end operational flows are not yet complete.

A Terraform configuration shows what the system is supposed to do. A live exercise shows what it actually did. I keep those statements separate.

## Results at a glance

| Project | Proven in AWS or GitHub | Still not proven live |
| --- | --- | --- |
| **1 — Cloud foundation** | Private EC2 servers in two AZs; HTTPS; WAF block; application logs and flow logs; a CloudWatch alarm changing state; encrypted RDS snapshot restore with a verified record | Automatic CloudWatch-to-AI delivery; independent AWS Backup restore; point-in-time recovery; database failover; application-to-database transaction |
| **2 — ECS delivery** | Private Fargate tasks across two AZs; HTTPS; GitHub OIDC deployment; immutable image; successful release; ECS rollback from a deliberately broken revision | GitHub workflow's own failed-smoke-test rollback; scale-out and scale-in under load; stage/prod controls |
| **3 — Governance** | Terraform policy tests and offline Python tests for security triage, cost analysis, permissions and failure handling | Real account creation/enrollment, SCP enforcement, delegated services, cross-account access and live dashboard sign-in |
| **Integration across stages** | Each workload was demonstrated independently with real AWS services | A single application running first on EC2 and then on ECS, with verified database interaction |

**Project 3 was deliberately tested offline.** Its code describes a multi-account architecture; it is not evidence of a deployed six-account organization.

## Project 1 — What happened

On **November 8, 2026**, I deployed an isolated dev environment. Two private EC2 instances served HTTPS traffic from different Availability Zones. A harmless WAF test returned **403**, and the application health check returned **200**. CloudWatch recorded an alarm entering and leaving the alarm state.

I created an RDS snapshot, restored it into a separate private database, and read back a known synthetic record. The measured restore time was **10 minutes 2 seconds** from restore request to verified read. This does **not** measure application cutover or total disaster-recovery time.

The deployed AI Lambda was invoked directly with synthetic alarm data. After a targeted KMS permission correction, its fallback report was stored in encrypted S3 and DynamoDB. In a separate **local handler test after teardown**, a live model response passed validation and was also persisted. Neither test proves automatic EventBridge delivery.

An account-level Lambda concurrency restriction blocked the reserved concurrency setting. Also, the alarm seen during the live exercise was not among the alarm names configured for AI EventBridge delivery. Both need attention before claiming an end-to-end automated incident workflow.

The AWS Backup vault had **no recovery points** during this exercise. Scheduled backup recovery, point-in-time restore and AZ failover remain untested.

[Full Project 1 test notes and evidence](PROJECT-1-LIVE-2026-11-08.md)

## Project 2 — What happened

On **November 8, 2026**, I deployed a containerized Flask service using GitHub Actions and ECR. Two private ECS tasks across separate AZs served the expected release over HTTPS. The WAF blocked a synthetic attack request.

A deliberately broken ECS revision failed to start. ECS automatically restored the previous working revision in **13 minutes 47 seconds**. This demonstrates the **ECS circuit breaker**, not the separate rollback step in the GitHub Actions workflow.

The first container encountered a real read-only-filesystem issue involving Gunicorn temporary files. I corrected the runtime configuration and repeated the launch. That failure and fix are part of the engineering evidence.

After teardown, a newer Debian Trixie-based image was built, started in CI, and rescanned. The ECR Linux/amd64 image findings changed from **9 HIGH** to **2 HIGH**, with **0 CRITICAL** in both scans. The two remaining findings affect glibc. **The newer image was not redeployed to ECS.** Fix or assess those findings before production promotion.

[Full Project 2 test notes and scan evidence](PROJECT-2-LIVE-2026-11-08.md)

## Project 3 — What the tests mean

Terraform 1.6.6 plan tests exercise the same SCP module used by the Organizations configuration. Python tests cover incident severity protections, AI fallbacks, cost-data handling, reporting and access-related configuration.

These are worthwhile automated tests. They do **not** demonstrate that AWS actually enforced the policies across separate accounts.

[Offline test commands](DEPLOYMENT.md#project-3-offline-validation)

## What the green GitHub check really means

The latest reviewed `CI - Test and Scan` run succeeded. It covers Python tests, dependency checks, container build, a container health check, an image scan, and offline Project 3 tests.

There are two important qualifications:

- The broad Terraform quality-gate job runs **only when manually requested**. A green default workflow does not mean that job ran.
- Checkov is configured with `soft_fail: true`, so its infrastructure security findings are **advisory**, not a blocking pass/fail gate.

The container scan also uses an ignore-unfixed policy. The separate ECR scan is the source of the two outstanding high findings.

[Latest reviewed CI run](https://github.com/JNHolman/RSVP-Cloud-Platform/actions/runs/42461692898)

## What's left to validate

**First, complete the shared application story:** use one small application across EC2 and ECS and verify that it really reads and writes test data. This is a planned improvement, not a tested integration.

The most useful additional demonstrations are:

1. **Project 1:** CloudWatch alarm → EventBridge → Lambda → AI result → persisted report / operator notification.
2. **Project 1:** AWS Backup restore, point-in-time restore and controlled Multi-AZ failover.
3. **Project 2:** GitHub workflow-triggered rollback and bounded autoscaling under load.
4. **Project 2:** Rescan the patched image when upstream fixes become available; document any remaining exposure.

These are **open tests**, not claims of completed work. Any live exercise requires a separate cost and safety review.

## Cost and cleanup

The November 8 planning worksheet estimated approximately **$0.72/hour** for Project 1 and **$0.18/hour** for Project 2 while the full demo workloads were running, before variable usage and restore overhead. These estimates are **not billed totals** and should not be reused without checking current pricing.

Both demo workloads were torn down. Some resources were deliberately retained: encrypted snapshots and backups, KMS keys, Terraform state storage, logs, evidence buckets, ECR images, the child DNS zone and related supporting components. They can still incur charges.

The original exercise planning target was **$75 combined**. Cost Explorer did not provide reliable per-project attribution on November 8 because the project cost-allocation tag was inactive. The recorded billing-review date was **November 15, 2026**; actual costs remain unverified in these documents.

Preserve the encryption keys needed to recover retained snapshots or read encrypted evidence. Deleting a running resource is not the same as removing every ongoing charge.

## Before another AWS deployment

This AWS account also hosts **RSVP Society production**. Existing Society resources, parent DNS records and shared infrastructure are out of scope.

A November 7 read-only preflight found an older `rsvp-dev-asg` with missing target-group dependencies and no verified Terraform ownership. **Do not adopt, repair or destroy it based on its name or tags.** The later Project 1 exercise used a separate `rsvp-pf1-dev` prefix and backend key, and then removed its demo workloads.

Follow the [deployment and safe-cleanup guide](DEPLOYMENT.md). It preserves the isolated state, DNS and retained-recovery boundaries.

## Evidence files

- [Project 1 live narrative](PROJECT-1-LIVE-2026-11-08.md) and [raw observations](evidence/project-1-2026-11-08/observations.json)
- [Project 2 live narrative](PROJECT-2-LIVE-2026-11-08.md), [raw observations](evidence/project-2-2026-11-08/observations.json) and [image scan comparison](evidence/project-2-2026-11-08/image-rescan.json)

The screenshots and raw observations are retained with the test reports. Published examples use synthetic data. The distinction between a tested result and an intended design is deliberate.
