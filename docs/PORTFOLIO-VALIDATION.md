# Portfolio validation and operating budget

I keep the evidence for a control alongside the claim it supports. A Terraform plan can show the intended boundary. A successful request through the deployed boundary requires a separate observation.

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

## Read-only preflight, November 7, 2026

The original checkout and this portfolio checkout share base commit `01da9bf`. The original Project 1 working directory has cached S3 backend configuration for the dedicated portfolio bucket in us-east-1, key `project-1-cloud-platform/dev/terraform.tfstate`, default workspace. Initialization records the backend connection locally. The remote bucket listing returned no versions or delete markers, so it supplied no workload state or lineage for an import or migration. The original checkout also has local edits and provider lock files. Keep that working directory intact.

A direct Auto Scaling query found `rsvp-dev-asg` with desired capacity two and zero attached instances. Its three most recent scaling activities failed validation because one or more target groups were missing. The dev instance profile has Project=rsvp and Environment=dev tags. Neither tags nor a matching name establish Terraform ownership. No DB instance or ALB with the rsvp-dev prefix appeared in the regional service queries. A general tagging query also missed the ASG, so use direct service inventory when reconciling other resource types.

Before any live Project 1 run, recover the owning deployment record or state backup if available. Match resource IDs and immutable configuration against the candidate addresses. If ownership can be demonstrated but state cannot be recovered, prepare an explicit adoption or retirement proposal with the owner for each surviving resource. Never adopt the group based on name alone. Repairing its target group while desired capacity remains two could trigger paid launches. The live health and restore claims remain outstanding.

The IAM OIDC provider listing was empty in the verified account. Project 2's existing bootstrap creates the provider and environment-scoped roles. Refresh that inventory immediately before an authorized bootstrap. If a provider has appeared in another stack, resolve ownership first. Existing GitHub Environments alone cannot issue working AWS sessions without provider and role trust.

## Project 1 portfolio deployment configuration

Use `infrastructure/project-1-cloud-platform/environments/portfolio-dev` for the new demonstration. It sets project_name to `rsvp-pf1` and environment to `dev`, producing the resource prefix `rsvp-pf1-dev`. Its proposed isolated VPC is 10.83.0.0/16. Confirm address availability against any networks that will be connected. The new state object key is `project-1-cloud-platform/portfolio-dev/terraform.tfstate` in the existing Cloud Platform backend. The three legacy scaling failures are evidence about the old dev deployment only. That deployment's ownership investigation can proceed independently.

For a future authorized plan, work from the new portfolio checkout, keep the default workspace and use a fresh TF_DATA_DIR dedicated to this configuration. Copy the values example to `environments/portfolio-dev/terraform.tfvars`, then supply the delegated child zone ID and dedicated secret ARN. Both workload roots disable overwrite when creating ACM validation records. If a record already exists, reconcile its owner before proceeding. Confirm the child zone, dev hostname, prefix, state key and account, and reconcile any existing portfolio-prefixed resources. Use the portfolio backend and variable files together:

```sh
# From infrastructure/project-1-cloud-platform in the portfolio checkout
export TF_DATA_DIR="$PWD/.terraform/portfolio-dev"
terraform init -backend-config=environments/portfolio-dev/backend.hcl
terraform workspace show
terraform plan -var-file=environments/portfolio-dev/terraform.tfvars -out=portfolio-dev.tfplan
```

The local backend.hcl is prepared in this checkout and ignored by Git. On another machine, fill the matching example from the dedicated backend outputs. Review the saved plan for object replacements, shared DNS writes, unexpected names and costs. The legacy dev key belongs only to the older configuration.

### Review the first workload plan locally

From the repository root, stream the saved plan into the reviewer. Supply the child zone ID verified independently against the delegated public zone. Select p1 for the isolated Project 1 demo or p2 for the Project 2 dev runtime.

```sh
set -o pipefail
terraform show -json "$PLAN_FILE" | python3 scripts/review-portfolio-plan.py p1 "$CHILD_ZONE_ID"
```

Run terraform show from an initialized workload directory if provider schemas are needed, using terraform -chdir and an absolute plan path. Streaming keeps the JSON, which may contain sensitive values, out of files and logs. Exit 1 flags a scope or action finding; exit 2 signals invalid input. Routine updates, replacements and deletions need a separate review from this first-deployment procedure. ACM can determine its validation name only after certificate creation. Its scoped record must have overwrite disabled. Review IAM permissions, shared dependencies, budget and backend identity separately.

Read the [November 8 live exercise record](PROJECT-1-LIVE-2026-11-08.md) for the observed outcomes and limitations.

## Shared-account and DNS prerequisites

1. Confirm the caller account, role and region before planning. This account also hosts Society production. Identify every existing rsvp-dev resource by ARN, tags and Terraform address. Compare the initialized checkout's backend bucket, dev key, workspace and state lineage against the dedicated Cloud Platform backend. The earlier current-object listing was empty. Check object versions and known state history with the owner. For the legacy namespace, an empty state alongside existing resources is a stop condition. For portfolio-dev, match inventory to its distinct resource prefix and key. Keep raw state, secrets and saved plans private.
2. Record existing parent DNS answers for the apex, www, api and proposed child. Resolve the authoritative parent with dig NS rsvpsociety.com. Inspect Squarespace for an existing cloud record, child delegation or DNSSEC DS. Resolve conflicts with the owner before changes. For a later authorized run only, create one public child zone cloud.rsvpsociety.com, then enter its four assigned servers as NS records at host cloud in Squarespace. Leave the parent nameservers and existing production records in place.
3. Compare dig +trace NS cloud.rsvpsociety.com and direct child-authority SOA answers, then repeat the parent-record checks. Supply only the child zone ID to the dev example. Verify ACM validation CNAMEs from public resolvers, regional certificate status ISSUED, dev/ecs aliases, TLS hostname and /health before recording evidence. Allow DNS propagation ahead of the paid workload windows.
4. P1 requires a dedicated Secrets Manager ARN, access to its encryption key, and a supported DB class/engine combination. P2 requires the existing dev GitHub Environment, matching role ARN, AWS_REGION, PROJECT_NAME and SERVICE_URL=https://ecs.cloud.rsvpsociety.com. Review environment branch/reviewer rules and OIDC audience and exact repository/environment subject. Limit bootstrap environments to dev. Check ownership of the account-singleton GitHub OIDC provider before bootstrap. If another stack owns it, pause before planning creation or import. Publish the scanned first immutable image before runtime planning. Use separate dev state keys for bootstrap and runtime.
5. Inspect the saved workload plan locally for account, DNS zone, resource names, replacements, IAM changes and access to existing resources. Keep Society buckets, databases, DNS, IAM roles, workflows and backend outside every plan. A shared AWS account still shares quotas, billing and some account-wide services.

## Evidence collection windows

| Sequential window | Earliest practical observation after provisioning | Evidence to retain |
|---|---|---|
| P1, reserve 4 hours including provisioning and cleanup | 10–15 min steady state for health, private placement, ALB requests, WAF sample and flow logs. Allow 10–20 min for an isolated test alarm and sanitized AI artifact. | Timestamped target health by AZ, private ENIs, request ID and log, alarm history and analysis status. Record fallback as fallback. |
| P1 recovery within the same window | Allow 45–120 min for an on-demand recovery point and a disposable private restored DB. Verify a known synthetic row and record backup/restore timestamps. | Recovery-point ARN, KMS status, measured recovery time and recoverable timestamp. Stop if the window expires and mark restore unverified. |
| P2, reserve 2 hours after P1 compute is removed | Allow 15–30 min for healthy service and metrics, 10–20 min for one good immutable release, 15–30 min for a controlled failing dev revision and recovery. | OIDC identity, environment approval, ECR digest/scan, two healthy private task ENIs, service events, SHA returned by HTTPS, prior revision restored and matching healthy response. Distinguish native circuit-breaker recovery from workflow smoke-test rollback. |
| P3 | Local only | Terraform test output and pytest results. Keep fixtures labeled synthetic. |

Use a dev-only disposable revision for failure injection during a separately authorized exercise. A manual rollback demonstrates operator recovery only. Record gaps if account permissions, DNS propagation, delayed logs or service startup prevent the intended observation. Redact account identifiers and personal or model-input data before publishing.

## Cost worksheet

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

## Teardown and custody

1. Record ownership, active revisions, backend key, resource addresses, backup identifiers, encryption keys and evidence custodian before any removal. Verify snapshot completion and recovery evidence. The final snapshot and retained automated backups have separate lifecycles. Daily AWS Backup points expire after 35 days; manual final snapshots require a deliberate retention decision.
2. For a future cleanup, prepare an explicit dev-only teardown plan with a reviewed address list for expendable resources. Separate retained recovery resources and their dependencies before execution. A whole-root destroy is blocked by protected keys. Avoid state removal as a deletion workaround. Keep the vault with its recovery points and all required KMS keys, grants and restore access. Confirm the final snapshot name is available and retain the DB key through the final snapshot. Preserve encrypted AI evidence and its key together.
3. Remove disposable restored DBs, app compute, load balancers, NAT gateways and unused EIPs. For P2 remove runtime before delivery infrastructure. Versioned nonempty buckets, retained vaults and nonempty ECR repositories can block deletion. Inventory object versions, delete markers and images. Retain evidence with an owner and expiry, and review deletion separately. Keep the shared backend, locks and OIDC identity provider. Remove child workload DNS records only after traffic has ended; parent NS removal requires separate DNS-owner coordination.
4. Verify by dev tags **and** recorded ARNs that ASGs/tasks, DB instances including restores, ALBs, NAT gateways and EIPs are gone. Confirm final snapshots, KMS availability and backup retention, reconcile remaining state and record ongoing charges. Keep protected keys under Terraform management. Ultimate retirement requires a separately reviewed retention decision after the last dependent recovery point, snapshot or encrypted artifact expires. Removing prevent_destroy or scheduling a key deletion during the demo would invalidate recovery evidence.
