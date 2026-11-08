# Project 1 — Cloud Foundation

```text
Internet → HTTPS/WAF → ALB → private EC2 (AZ A + AZ B)
                                   ↓
                         encrypted Multi-AZ RDS
```

The VPC isolates application and database resources. Security groups restrict traffic; CloudWatch and flow logs support troubleshooting. Backups and snapshots support recovery.

**Incident path:** CloudWatch alarm → EventBridge → Lambda → bounded log/metric evidence → validated AI or deterministic fallback → encrypted S3 and DynamoDB. AI is advisory and cannot change infrastructure.

**Live evidence:** Private targets in two AZs, HTTPS, WAF rejection, alarms, and a snapshot restore verified against a known record in **10m 02s**. Daily backup delivery, point-in-time recovery, and AZ failover are design capabilities, not all independently proven by that exercise.

## Evidence checklist

[Exercise report and homepage screenshot](evidence/2026-11-08.md) · [Recorded observations](evidence/observations.json)

| Area | Evidence available | Evidence still needed |
|---|---|---|
| Networking and security | Two private targets in different AZs, issued certificate, WAF 403, active flow logs | Capture an AZ/target view if another exercise is authorized |
| Monitoring and AI | Alarm history, direct Lambda fallback, encrypted S3/DynamoDB persistence and a separate live-model handler test | Correlate a real alarm with invocation, model result and subscriber delivery |
| Recovery | Restored a known marker over TLS in 10m 02s | AWS Backup restore, PITR, Multi-AZ failover and application cutover |

## Operations

**Location:** `project-1-cloud-foundation/terraform/`

### Portfolio-dev configuration

Use `environments/portfolio-dev/`, not the older `dev/` backend. The portfolio prefix is `rsvp-pf1-dev`, and the state key is `project-1-cloud-platform/portfolio-dev/terraform.tfstate`. The proposed VPC CIDR is `10.83.0.0/16`; confirm it does not conflict with networks the VPC may connect to.

Prepare local copies of `backend.hcl.example` and `terraform.tfvars.example`, leaving the examples untouched. Set the delegated child-zone ID, `dev.cloud.rsvpsociety.com`, and a **dedicated** Secrets Manager ARN for the AI credential. Keep these values out of Git.

After filling in and checking those local files:

```sh
cd project-1-cloud-foundation/terraform
export TF_DATA_DIR="$PWD/.terraform/portfolio-dev"
terraform init -backend-config=environments/portfolio-dev/backend.hcl
terraform workspace show
terraform plan -var-file=environments/portfolio-dev/terraform.tfvars -out=portfolio-dev.tfplan
```

To check the intended first-deployment scope, review the plan and run the local reviewer with the independently confirmed child-zone ID:

```sh
set -o pipefail
terraform show -json portfolio-dev.tfplan | python3 ../../shared/review-portfolio-plan.py p1 "$CHILD_ZONE_ID"
```

A scope finding means **stop and review**, not override the check. Keep plans and raw state private; they may contain sensitive values.

Only after an explicit approval should anyone apply the reviewed plan.

**What to verify:** HTTPS health; two healthy private instances in different AZs; WAF response; application and VPC logs; a working app-to-database request; alarm-to-AI delivery and saved report; RDS encryption and managed credentials; AWS Backup recovery, point-in-time restore, and a controlled failover. Record observed results separately from configuration checks.

The historical EC2 page and the database marker were tested separately. An application-to-database claim requires a request that returns a row from RDS.


The plan reviewer is intended for first-deployment scope checks, not automatic approval of updates or deletions. It may return exit 1 for scope/action findings and exit 2 for invalid input. Keep the JSON stream out of saved logs; review IAM, budget, backend identity, shared dependencies, and ACM DNS record ownership separately.

[Platform overview](../README.md) · [Shared state, DNS, costs and teardown](../shared/OPERATIONS.md)
