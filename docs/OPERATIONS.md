# Operations — deployment, validation, recovery, and costs

This runbook is for someone reproducing the AWS exercises or reviewing the engineering. The business story is in the [main README](../README.md), and the design decisions are in [Architecture](ARCHITECTURE.md).

The project follows one application's evolution from EC2 hosting to ECS delivery, with enterprise operations built around it. Use isolated environment configuration and explicit resource ownership rather than forcing the two hosting models to run at once.

The commands below reflect the documented AWS test environments. Follow the matching application and infrastructure configuration in the repository and review the Terraform plan before any AWS changes.

## Historical live-test baseline

The dated November 8 AWS exercises deployed Projects 1 and 2 in isolated dev environments. Temporary workloads were removed after testing. Selected snapshots, encryption keys, logs, images, DNS, and Terraform backend resources were retained.

Project 3's enterprise account architecture is validated through offline tests. That avoids creating six paid AWS accounts for a portfolio exercise.

**Never use these steps to change RSVP Society production.**

## Before changing AWS

1. **Identify the account and region.** Use `aws sts get-caller-identity`. The exercises used `us-east-1`.
2. **Confirm ownership.** Record the Terraform backend bucket and key, workspace, resource names and ARNs. Check existing resources independently. An empty or mismatched state file is a stop condition when matching resources already exist.
3. **Protect RSVP Society.** No changes to its databases, IAM roles, state, buckets, parent DNS records or live services.
4. **Check costs.** Refresh AWS prices, quotas and retained-resource charges. Keep the combined demonstration target under **$75**, but do not assume a short test will automatically stay within budget.
5. **Review the plan before every apply.** Examine the resources to be created, changed or deleted, plus DNS, IAM, ownership and encryption dependencies. Do not run a broad `terraform destroy` against a stack containing protected recovery artifacts.

The November 7 preflight found an older `rsvp-dev-asg` whose state ownership was not established. Leave that legacy resource alone. Use the dedicated portfolio namespace for Project 1.

## Tests before deployment

Open a review branch and check **CI - Test and Scan**. Its normal run covers Python checks, tests and dependency auditing, the container build and image scan, and Project 3's offline module tests.

**Do not confuse green CI with every check being enforced.** Full Terraform quality gates require a manual workflow dispatch with `run_terraform=true`. Checkov findings are advisory because that job uses `soft_fail: true`. The container scan ignores findings without a known fix. Review those reports separately.

No Terraform apply or destroy is performed automatically by these workflows.

## Shared setup: state and DNS

Every Terraform root must use the correct backend and workspace. Bootstrap `infrastructure/bootstrap-state` only in the account that will own that state, and retain its outputs:

- `state_bucket_name`
- `lock_table_name`
- `state_kms_key_arn`

Copy a root's `backend.hcl.example` to a **local, untracked** `backend.hcl`. Replace the bucket and KMS placeholders using outputs from the correct backend. Do not copy an existing production backend merely because it is convenient.

The demos used a delegated `cloud.rsvpsociety.com` child zone. Confirm that the existing parent delegation and child records are correct. The portfolio uses `dev.cloud.rsvpsociety.com` for Project 1 and `ecs.cloud.rsvpsociety.com` for Project 2. Do not replace the parent nameservers or change Society's apex, www or API records. Check ACM validation records for collisions; record ownership before changing DNS.

### Detailed shared-account and DNS checks

1. Confirm the caller account, role and region before planning. This account also hosts Society production. Identify every existing rsvp-dev resource by ARN, tags and Terraform address. Compare the initialized checkout's backend bucket, dev key, workspace and state lineage against the dedicated Cloud Platform backend. The earlier current-object listing was empty. Check object versions and known state history with the owner. For the legacy namespace, an empty state alongside existing resources is a stop condition. For portfolio-dev, match inventory to its distinct resource prefix and key. Keep raw state, secrets and saved plans private.
2. Record existing parent DNS answers for the apex, www, api and proposed child. Resolve the authoritative parent with dig NS rsvpsociety.com. Inspect Squarespace for an existing cloud record, child delegation or DNSSEC DS. Resolve conflicts with the owner before changes. For a later authorized run only, create one public child zone cloud.rsvpsociety.com, then enter its four assigned servers as NS records at host cloud in Squarespace. Leave the parent nameservers and existing production records in place.
3. Compare dig +trace NS cloud.rsvpsociety.com and direct child-authority SOA answers, then repeat the parent-record checks. Supply only the child zone ID to the dev example. Verify ACM validation CNAMEs from public resolvers, regional certificate status ISSUED, dev/ecs aliases, TLS hostname and /health before recording evidence. Allow DNS propagation ahead of the paid workload windows.
4. P1 requires a dedicated Secrets Manager ARN, access to its encryption key, and a supported DB class/engine combination. P2 requires the existing dev GitHub Environment, matching role ARN, AWS_REGION, PROJECT_NAME and SERVICE_URL=https://ecs.cloud.rsvpsociety.com. Review environment branch/reviewer rules and OIDC audience and exact repository/environment subject. Limit bootstrap environments to dev. Check ownership of the account-singleton GitHub OIDC provider before bootstrap. If another stack owns it, pause before planning creation or import. Publish the scanned first immutable image before runtime planning. Use separate dev state keys for bootstrap and runtime.
5. Inspect the saved workload plan locally for account, DNS zone, resource names, replacements, IAM changes and access to existing resources. Keep Society buckets, databases, DNS, IAM roles, workflows and backend outside every plan. A shared AWS account still shares quotas, billing and some account-wide services.

## Project 1: isolated cloud foundation

**Location:** `infrastructure/project-1-cloud-platform/`

### Portfolio-dev configuration

Use `environments/portfolio-dev/`, not the older `dev/` backend. The portfolio prefix is `rsvp-pf1-dev`, and the state key is `project-1-cloud-platform/portfolio-dev/terraform.tfstate`. The proposed VPC CIDR is `10.83.0.0/16`; confirm it does not conflict with networks the VPC may connect to.

Prepare local copies of `backend.hcl.example` and `terraform.tfvars.example`, leaving the examples untouched. Set the delegated child-zone ID, `dev.cloud.rsvpsociety.com`, and a **dedicated** Secrets Manager ARN for the AI credential. Keep these values out of Git.

After filling in and checking those local files:

```sh
cd infrastructure/project-1-cloud-platform
export TF_DATA_DIR="$PWD/.terraform/portfolio-dev"
terraform init -backend-config=environments/portfolio-dev/backend.hcl
terraform workspace show
terraform plan -var-file=environments/portfolio-dev/terraform.tfvars -out=portfolio-dev.tfplan
```

To check the intended first-deployment scope, review the plan and run the local reviewer with the independently confirmed child-zone ID:

```sh
set -o pipefail
terraform show -json portfolio-dev.tfplan | python3 ../../scripts/review-portfolio-plan.py p1 "$CHILD_ZONE_ID"
```

A scope finding means **stop and review**, not override the check. Keep plans and raw state private; they may contain sensitive values.

Only after an explicit approval should anyone apply the reviewed plan.

**What to verify:** HTTPS health; two healthy private instances in different AZs; WAF response; application and VPC logs; a working app-to-database request; alarm-to-AI delivery and saved report; RDS encryption and managed credentials; AWS Backup recovery, point-in-time restore, and a controlled failover. Record observed results separately from configuration checks.

For application verification, use the shared application's health, version, and database operations. Check the actual database response rather than treating a successful landing-page request as proof that the data path works.

[Previously recorded Project 1 results](PROJECT-1-LIVE-2026-11-08.md)

The plan reviewer is intended for first-deployment scope checks, not automatic approval of updates or deletions. It may return exit 1 for scope/action findings and exit 2 for invalid input. Keep the JSON stream out of saved logs; review IAM, budget, backend identity, shared dependencies, and ACM DNS record ownership separately.

## Project 2: isolated ECS delivery

Before using the production OIDC role, configure **GitHub Environment protection rules for `prod`**: **restrict deployment branches/tags** to approved release sources and require reviewer approval where supported. Environment protection is part of the **production authorization boundary**, because AWS trust scopes the OIDC subject to the repository and environment.


**Locations:** `infrastructure/project-2-ecs-cicd/bootstrap-delivery/` and `infrastructure/project-2-ecs-cicd/terraform/`

1. **Bootstrap delivery.** Use the bootstrap Terraform root in the intended AWS account. It manages the ECR repositories, the GitHub OIDC provider and environment-specific deployment roles. Confirm the account does not already have an independently owned OIDC provider before making changes.
2. **Configure GitHub.** Set `AWS_DEPLOY_ROLE_ARN` in the matching GitHub Environment. Also set `AWS_REGION` and `PROJECT_NAME` if not using the defaults (`us-east-1`, `rsvp-project2`). For stage/prod, restrict approved branches/tags and require approval where supported.
3. **Build the first image.** Run **ECS Project 2 - Bootstrap First Image** for the target environment. Copy the exact immutable Git-SHA image URI into the local runtime `terraform.tfvars` as `container_image`. Do not use `:latest`.
4. **Deploy the runtime.** Initialize `infrastructure/project-2-ecs-cicd/terraform/` with its matching dev backend, review its plan, and apply only after approval.
5. **Finish GitHub configuration.** Set `SERVICE_URL` to the service's verified HTTPS URL. Run **ECS Project 2 - Controlled Deploy**, then confirm that `/health` returns the expected release and environment.

**What to verify:** Two healthy private tasks in separate AZs, HTTPS, WAF, logs, the ECR image digest and GitHub's deployment result. The ECS circuit-breaker rollback and GitHub workflow rollback are separate behaviors. Verify each through its own controlled failure path. Use bounded load for autoscaling and record both scale-out and scale-in events.

**Important:** Terraform sets the ECS baseline. The GitHub workflow owns application releases. The ECS service intentionally ignores later task-definition drift so a Terraform-only change does not unexpectedly revert a release. After changing the Terraform task baseline, run Controlled Deploy before claiming that baseline is active.

[Previously recorded Project 2 results](PROJECT-2-LIVE-2026-11-08.md)

## Project 3 offline validation

The six-account design is **not deployed** for this portfolio. With Terraform 1.6.6 and the project's Python test dependencies installed, run from the repository root:

```sh
(cd infrastructure/project-3-cloud-governance/modules/scp-policies && terraform init -backend=false && terraform validate && terraform test)
python -m pytest -q tests
```

These tests prove policy generation and local application logic. They do not prove that AWS enforced the policies across accounts.

### If deploying Project 3 in a real organization

For each Project 3 root, copy `backend.hcl.example` to an untracked `backend.hcl`. Replace the bucket placeholder and `REPLACE_WITH_TERRAFORM_STATE_KMS_KEY_ARN` with that account's **state-bootstrap outputs** before initializing Terraform. Do not reuse another account's backend without reviewing cross-account access.

When `create_member_accounts=false`, the organization stack references existing accounts; it **does not move those accounts**. Verify their OU placement: **An account outside the target OU will not inherit that OU's SCPs.** If StackSets delegated administration is enabled, activate CloudFormation trusted access (`ActivateOrganizationsAccess`) before enabling delegated administration.


Only use a separately approved enterprise environment. Each root needs a backend in the **account where it runs**, not an assumed shared management-account backend:

| Account | Terraform roots |
| --- | --- |
| Management | `organization`, `audit-trail`, `finops-ai`, `identity-center` |
| Security | `security-admin` |
| Log Archive | `log-archive` |
| Workload | `workload` |

Use this deployment order: **organization → log-archive → audit-trail → security-admin → finops-ai → identity-center → workload**.

When referencing existing accounts, confirm OU membership: Terraform does not automatically move accounts merely because their IDs were supplied. Confirm delegated-administrator prerequisites, StackSets trusted access where used, and explicit account-scoped SCP exceptions. Configure Security and FinOps dashboard read roles before creating the workload dashboard API. No such live deployment is claimed here.

## Validation and recovery

The dated exercise results below are measured historical outcomes. The integration checks that follow describe the final application contract; only dated live evidence establishes measured runtime results.

## Recorded live AWS results — November 8, 2026

These are the **measured results from the original deployment sessions**. They stay attached to the date and version tested, even when the code changes later.

| What I tested | What happened | Evidence |
| --- | --- | --- |
| Private application servers | Two healthy EC2 instances served the test page from different Availability Zones, without public IP addresses | [Project 1 exercise](PROJECT-1-LIVE-2026-11-08.md) |
| Secure web traffic | HTTPS returned a healthy response; WAF blocked a harmless simulated attack | [Project 1 exercise](PROJECT-1-LIVE-2026-11-08.md) |
| Database recovery | A known record survived a restore to a separate encrypted RDS database. Request to verified read: **10m 02s** | [Project 1 recovery timeline](PROJECT-1-LIVE-2026-11-08.md#recovery-timeline) |
| Monitoring | CloudWatch recorded an unhealthy-target alarm entering and leaving the alarm state | [Project 1 observations](evidence/project-1-2026-11-08/observations.json) |
| AI handler and persistence | A direct Lambda test produced a stored, encrypted fallback report; a separate local handler test exercised a live model response | [Project 1 exercise](PROJECT-1-LIVE-2026-11-08.md) |
| Automated container deployment | GitHub Actions authenticated through OIDC, built and scanned an image, then deployed it to private ECS tasks | [Project 2 exercise](PROJECT-2-LIVE-2026-11-08.md) |
| Failed release recovery | A deliberately broken ECS revision recovered to the previous healthy version in **13m 47s** | [Project 2 exercise](PROJECT-2-LIVE-2026-11-08.md) |
| Container security review | A newer image reduced ECR's HIGH findings from nine to two, with no CRITICAL findings in either image scan | [Project 2 scan comparison](evidence/project-2-2026-11-08/image-rescan.json) |
| Enterprise governance | Terraform and Python tests exercised policies, security analysis, fallback responses, and reporting without deploying six accounts | [Offline test guide](#project-3-offline-validation) |

The original exercises also uncovered actual problems: an AWS Lambda concurrency limit, a KMS permission issue, a container temporary-file failure, and container package vulnerabilities. The dated reports show those failures and how they were handled. That troubleshooting is part of the project, not something to hide.

### Original validation classification matrix

This matrix records the scope of the November 8 exercise and its offline checks. An unverified live integration in this historical snapshot is not a claim that later Codex work failed; newer results require separate dated evidence.

| Capability | Classification | Evidence available or still required |
|---|---|---|
| Dedicated portfolio backend exists | Live validated, inventory only | Read-only inspection identified the state and access-log buckets and lock table. The original checkout's cached S3 backend configuration matches the dev key. The bucket returned no object versions or delete markers. Workload state lineage and ownership remain unresolved. |
| P1 two-AZ private ASG, ALB, HTTPS, WAF, application logging and flow logs | Live validated | Two healthy targets across two AZs without public IPs, HTTPS 200, synthetic XSS 403, ALB alarm transition and flow-log delivery. |
| P1 encrypted Multi-AZ MySQL and snapshot recovery | Live validated | A known row persisted through a restore to a separate private instance. Restore request to verified read took 10m 02s. |
| P1 daily AWS Backup jobs, point-in-time restore and failover | Architecture validated | Live inventory showed 14-day automated retention and a restorable timestamp. The independent backup vault had zero points during the demo. Scheduled delivery, PITR and AZ failover still need exercises. |
| P1 AI deterministic fallback and persistence | Live validated, direct invocation | Synthetic input to the deployed Lambda produced an encrypted S3 object and DynamoDB metadata after a table-scoped KMS correction. |
| P1 external AI analysis | Live validated, local handler invocation | A synthetic alarm produced a schema-validated gpt-5.5 result persisted to KMS-encrypted S3 and DynamoDB. |
| P1 alarm-to-Lambda delivery | Not yet validated | The shared account could not reserve the configured concurrency. |
| P2 container health and headers | Automated validated | Flask tests exercise the HTTP routes. |
| P2 private Fargate, HTTPS ALB, WAF and telemetry | Live validated | Two healthy task ENIs across two AZs without public addresses, serving SHA matched, WAF probe returned 403 and application logs arrived. |
| P2 OIDC delivery, immutable ECR image and ECS release | Live validated in dev | GitHub assumed the environment-scoped role, built and scanned the image, then deployed the revision. The running digest matched ECR. See the [live run and scan findings](PROJECT-2-LIVE-2026-11-08.md). |
| P2 native failed-release recovery | Live validated | A controlled startup failure in revision 4 triggered ECS rollback to revision 3 in 13m 47s, with the expected HTTPS response after recovery. |
| P2 load-driven scaling, workflow-triggered smoke-failure rollback, stage/prod boundaries | Not yet validated live | The dev scaling range and alarm configuration were observed. Only the native circuit breaker failure path was exercised. |
| P3 six-account topology, OU attachment targets, service delegation and Identity Center grants | Automated validated, configuration contracts | Tests inspect actual Terraform blocks, opt-ins, assignment targets and managed policies. |
| P3 SCP denies and named exceptions | Automated validated, generated documents | Terraform 1.6.6 plan tests on the same module used by Organizations. |
| P3 CloudTrail, log archive, dashboard trust, least privilege and Cognito GET protection | Automated validated, configuration contracts | Tests check trail, archive key policies, exact role conditions, table permissions and GET authorizer wiring. |
| P3 GuardDuty findings imported through Security Hub, AI triage, FinOps, dashboard and fallbacks | Automated validated, local runtime | Synthetic events and recording clients exercise handler logic, pagination, severity floors, persistence, error sanitization and degraded responses. |
| P3 OU enforcement, STS decisions, service enrollment, CloudTrail delivery, Identity Center login and real token acceptance/rejection | Not yet validated | Enterprise integration environment required for multi-account claims. No Project 3 deployment planned. |

## Final integration and automation checks

The finished engineering work uses **one application contract across EC2 and ECS**. Its validation covers:

| Area | What the check demonstrates |
| --- | --- |
| Application and database | The same app can run in both hosting models and read/write synthetic MySQL data |
| AI incident handling | A matching alarm is routed to the handler, evidence is bounded and checked, and encrypted analysis results are saved and sent to an operator |
| Backup and recovery | AWS Backup, point-in-time recovery, and controlled database failover have a repeatable procedure with data checks and timing |
| GitHub deployment rollback | The release workflow can detect a failed smoke test and restore a healthy revision independently of ECS-native rollback |
| Scaling | A bounded test can drive ECS above its minimum task count and back down |
| Container security | Images are rebuilt and scanned; outstanding vendor findings are tracked rather than ignored |
| CI controls | Mandatory test gates fail when required checks fail; advisory checks are identified clearly |
| Governance | Terraform and local runtime tests validate enterprise policy and operations behavior without maintaining multiple AWS accounts |

**Test procedures and automated checks are different from a recorded live result.** The dated reports above remain the source for measured AWS outcomes. New live results should be added as new dated evidence rather than changing history.

## Validation windows and evidence to capture

| Sequential window | Earliest practical observation after provisioning | Evidence to retain |
|---|---|---|
| P1, reserve 4 hours including provisioning and cleanup | 10–15 min steady state for health, private placement, ALB requests, WAF sample and flow logs. Allow 10–20 min for an isolated test alarm and sanitized AI artifact. | Timestamped target health by AZ, private ENIs, request ID and log, alarm history and analysis status. Record fallback as fallback. |
| P1 recovery within the same window | Allow 45–120 min for an on-demand recovery point and a disposable private restored DB. Verify a known synthetic row and record backup/restore timestamps. | Recovery-point ARN, KMS status, measured recovery time and recoverable timestamp. Stop if the window expires and mark restore unverified. |
| P2, reserve 2 hours after P1 compute is removed | Allow 15–30 min for healthy service and metrics, 10–20 min for one good immutable release, 15–30 min for a controlled failing dev revision and recovery. | OIDC identity, environment approval, ECR digest/scan, two healthy private task ENIs, service events, SHA returned by HTTPS, prior revision restored and matching healthy response. Distinguish native circuit-breaker recovery from workflow smoke-test rollback. |
| P3 | Local only | Terraform test output and pytest results. Keep fixtures labeled synthetic. |

Use a dev-only disposable revision for failure injection during a separately authorized exercise. A manual rollback demonstrates operator recovery only. Record gaps if account permissions, DNS propagation, delayed logs or service startup prevent the intended observation. Redact account identifiers and personal or model-input data before publishing.

## Cost management

The worksheet below is a planning model. Actual charges require billing reconciliation.

## Cost worksheet — planning estimates, not actual charges

Planning estimates in USD for us-east-1 Linux x86 on demand, two AZs, 730 hours/month, November 2026. Assume four public IPv4 addresses per live workload (two ALB and two NAT), one LCU, low traffic and no credits. Check regional rates, actual AMI disk size and billing usage before starting.

| Component | P1 hourly | P2 hourly |
|---|---:|---:|
| Two NAT gateways at 0.045, four IPv4 at 0.005 | 0.110 | 0.110 |
| ALB at 0.0225 plus one LCU at 0.008 | 0.0305 | 0.0305 |
| Two t3.micro at 0.0104 plus assumed two 8 GiB gp3 root disks | 0.0226 | — |
| Multi-AZ db.t4g.medium MySQL, 20 GiB gp3 per copy | 0.129 + 0.0063 | — |
| MySQL 8.0 extended support allowance, two vCPU on primary and standby at 0.10/vCPU-hour | 0.40 | — |
| Two Fargate tasks, each 0.25 vCPU at 0.04048 and 0.5 GiB at 0.004445 | — | 0.0247 |
| One WAF ACL plus four rules, 9/month prorated | 0.0123 | 0.0123 |
| Customer-managed keys, four for P1 and two for P2 including ECR | 0.0055 | 0.0027 |
| Estimated running subtotal | **0.72/h** | **0.18/h** |

P1 four hours ≈ $2.88. A disposable single-AZ db.t4g.medium restore adds about $0.27/hour including two vCPUs of estimated Extended Support and 20 GiB of gp3. Allow $0.27–0.54 for one to two hours. P2 two hours ≈ $0.36. P3 incremental AWS cost $0. Shared child zone allowance $0.50 for the first month. There is no domain purchase or assumed setup fee. Add $5 per live project for metered usage and provisioning overruns. This gives approximately **$14.30 for the exercise** before ongoing retention, existing usage and tax. Actual billed time extends until deletion completes.

[Network pricing](https://aws.amazon.com/vpc/pricing/) · [ALB](https://aws.amazon.com/elasticloadbalancing/pricing/) · [EC2](https://aws.amazon.com/ec2/pricing/on-demand/) · [Fargate](https://aws.amazon.com/fargate/pricing/) · [RDS](https://aws.amazon.com/rds/mysql/pricing/) · [MySQL support dates](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/MySQL.Concepts.VersionMgmt.html) · [WAF](https://aws.amazon.com/waf/pricing/)

The usage allowance assumes under 1 GB each of NAT processing and log ingestion per project (roughly $0.045/GB and $0.50/GB respectively), light S3/KMS/API activity and brief alarm/dashboard operation. Also meter WAF requests, ECR storage/scanning, image pulls, data transfer, Secrets Manager, Lambda and DynamoDB. External AI calls bill separately to the API account. Extended Support for MySQL 8.0 is material at this size. Confirm availability and engine pricing before a restore. Do not upgrade an existing database solely to change this estimate.

Budget separately for retained assets. One state KMS key is roughly $1/month plus rotations and requests. State versions, access-log bytes, S3 requests and DynamoDB locks depend on measured usage. Two protected P1 keys add roughly $2/month before rotations. A full 20 GB snapshot-equivalent at $0.095/GB-month is $1.90/month; two independently billed equivalents would be $3.80. Retaining the Project 2 delivery bootstrap adds approximately $1/month for its ECR key plus image storage. Measure actual incremental backup bytes, retention, logs, ECR images and any additional keys required for decryption. Baseline example for month one ≈ $22 including the ECR key, the exercise, backend key, two recovery keys and two backup equivalents, plus variable retention and pre-existing usage. Review tagged and untagged charges the following day and after the first billing cycle. At $0.72/h, four and a half days of unattended P1 runtime alone approaches $75. Extended restore attempts, autoscaling, log floods and leftover NAT gateways can exhaust the target.

[KMS](https://aws.amazon.com/kms/pricing/) · [Backup](https://aws.amazon.com/backup/pricing/) · [CloudWatch](https://aws.amazon.com/cloudwatch/pricing/) · [DNS](https://aws.amazon.com/route53/pricing/)

## Cleanup and resource custody

## Evidence capture and cleanup overview

For each exercise, record the deployed revision, relevant resource ARNs, time-stamped outcomes, health checks, failures, recovery times and a small number of screenshots. Use synthetic data and remove account identifiers or secrets before publishing. A configuration screenshot is not proof that recovery worked.

Before cleanup, identify which resources are expendable and which must stay to protect evidence or backups:

- Remove **only** reviewed disposable demo workloads, including restored databases, compute, load balancers, NAT gateways and temporary public IP addresses.
- Retain required snapshots, backup recovery points, KMS keys, Terraform state and encrypted evidence until an owner approves their retirement. Project 1 has `prevent_destroy` guards on recovery keys.
- Expect versioned S3 buckets, ECR images, backup vaults and dependencies to prevent a simple whole-root destroy. Never remove Terraform state to bypass an ownership or deletion problem.
- Remove workload-specific DNS records only after the service is gone. Treat parent delegation as a separate DNS-owner decision.
- Verify cleanup using **resource ARNs and direct AWS inventory**, not tags alone. Check for remaining databases, tasks, ASGs, ALBs, NAT gateways and EIPs. Reconcile retained resources and continuing charges.

## Teardown and retained-resource custody

Project 1 recovery KMS keys have Terraform destruction guards; **do not expect an unrestricted `terraform destroy`** to remove protected keys, snapshots, or recovery points. Review retained data and encryption dependencies before retiring anything.


1. Record ownership, active revisions, backend key, resource addresses, backup identifiers, encryption keys and evidence custodian before any removal. Verify snapshot completion and recovery evidence. The final snapshot and retained automated backups have separate lifecycles. Daily AWS Backup points expire after 35 days; manual final snapshots require a deliberate retention decision.
2. For a future cleanup, prepare an explicit dev-only teardown plan with a reviewed address list for expendable resources. Separate retained recovery resources and their dependencies before execution. A whole-root destroy is blocked by protected keys. Avoid state removal as a deletion workaround. Keep the vault with its recovery points and all required KMS keys, grants and restore access. Confirm the final snapshot name is available and retain the DB key through the final snapshot. Preserve encrypted AI evidence and its key together.
3. Remove disposable restored DBs, app compute, load balancers, NAT gateways and unused EIPs. For P2 remove runtime before delivery infrastructure. Versioned nonempty buckets, retained vaults and nonempty ECR repositories can block deletion. Inventory object versions, delete markers and images. Retain evidence with an owner and expiry, and review deletion separately. Keep the shared backend, locks and OIDC identity provider. Remove child workload DNS records only after traffic has ended; parent NS removal requires separate DNS-owner coordination.
4. Verify by dev tags **and** recorded ARNs that ASGs/tasks, DB instances including restores, ALBs, NAT gateways and EIPs are gone. Confirm final snapshots, KMS availability and backup retention, reconcile remaining state and record ongoing charges. Keep protected keys under Terraform management. Ultimate retirement requires a separately reviewed retention decision after the last dependent recovery point, snapshot or encrypted artifact expires. Removing prevent_destroy or scheduling a key deletion during the demo would invalidate recovery evidence.

## Billing and retention review

On November 8, 2026, Cost Explorer returned estimated daily data with no groups for the rsvp-pf1 and rsvp-project2 project tags. The Project cost-allocation tag was inactive. The exact demo charge is unresolved. In this shared account, whole-account daily totals also include Society production activity.

**Next billing review: November 15, 2026.** Use the billing console or an existing cost-and-usage report to reconcile identifiable portfolio usage by resource ID, SKU and demo time window. Record any unattributable charges separately. Inventory the two manual RDS snapshots, retained automated backups, evidence buckets, CloudWatch logs, ECR images, hosted zone, secret and required KMS keys. Assign an owner and expiry decision to each retained item. Preserve encryption keys for every snapshot or artifact that must remain readable.

## Historical context

Retained for audit traceability; these November 7 observations precede the November 8 live tests and are not current operating instructions.

## Historical preflight — November 7, 2026

This is an archived observation, not a statement of current deployment status. The subsequent November 8 test results are recorded above.

At the time of the November 7 preflight, the original checkout and the portfolio checkout shared base commit `01da9bf`. The original Project 1 working directory has cached S3 backend configuration for the dedicated portfolio bucket in us-east-1, key `project-1-cloud-platform/dev/terraform.tfstate`, default workspace. Initialization records the backend connection locally. The remote bucket listing returned no versions or delete markers, so it supplied no workload state or lineage for an import or migration. The original checkout also has local edits and provider lock files. Keep that working directory intact.

A direct Auto Scaling query found `rsvp-dev-asg` with desired capacity two and zero attached instances. Its three most recent scaling activities failed validation because one or more target groups were missing. The dev instance profile has Project=rsvp and Environment=dev tags. Neither tags nor a matching name establish Terraform ownership. No DB instance or ALB with the rsvp-dev prefix appeared in the regional service queries. A general tagging query also missed the ASG, so use direct service inventory when reconciling other resource types.

Before any live Project 1 run, recover the owning deployment record or state backup if available. Match resource IDs and immutable configuration against the candidate addresses. If ownership can be demonstrated but state cannot be recovered, prepare an explicit adoption or retirement proposal with the owner for each surviving resource. Never adopt the group based on name alone. Repairing its target group while desired capacity remains two could trigger paid launches. Those live health and restore checks had not yet been completed on November 7; the November 8 results above supersede that preflight status.

The IAM OIDC provider listing was empty in the verified account. Project 2's existing bootstrap creates the provider and environment-scoped roles. Refresh that inventory immediately before an authorized bootstrap. If a provider has appeared in another stack, resolve ownership first. Existing GitHub Environments alone cannot issue working AWS sessions without provider and role trust.