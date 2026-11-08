# Deployment and testing — technical guide

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

## Project 1: isolated cloud foundation

**Location:** `infrastructure/project-1-cloud-platform/`

### Project 1 portfolio deployment configuration

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

## Project 2: isolated ECS delivery

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

Only use a separately approved enterprise environment. Each root needs a backend in the **account where it runs**, not an assumed shared management-account backend:

| Account | Terraform roots |
| --- | --- |
| Management | `organization`, `audit-trail`, `finops-ai`, `identity-center` |
| Security | `security-admin` |
| Log Archive | `log-archive` |
| Workload | `workload` |

Use this deployment order: **organization → log-archive → audit-trail → security-admin → finops-ai → identity-center → workload**.

When referencing existing accounts, confirm OU membership: Terraform does not automatically move accounts merely because their IDs were supplied. Confirm delegated-administrator prerequisites, StackSets trusted access where used, and explicit account-scoped SCP exceptions. Configure Security and FinOps dashboard read roles before creating the workload dashboard API. No such live deployment is claimed here.

## Capture proof and clean up

For each exercise, record the deployed revision, relevant resource ARNs, time-stamped outcomes, health checks, failures, recovery times and a small number of screenshots. Use synthetic data and remove account identifiers or secrets before publishing. A configuration screenshot is not proof that recovery worked.

Before cleanup, identify which resources are expendable and which must stay to protect evidence or backups:

- Remove **only** reviewed disposable demo workloads, including restored databases, compute, load balancers, NAT gateways and temporary public IP addresses.
- Retain required snapshots, backup recovery points, KMS keys, Terraform state and encrypted evidence until an owner approves their retirement. Project 1 has `prevent_destroy` guards on recovery keys.
- Expect versioned S3 buckets, ECR images, backup vaults and dependencies to prevent a simple whole-root destroy. Never remove Terraform state to bypass an ownership or deletion problem.
- Remove workload-specific DNS records only after the service is gone. Treat parent delegation as a separate DNS-owner decision.
- Verify cleanup using **resource ARNs and direct AWS inventory**, not tags alone. Check for remaining databases, tasks, ASGs, ALBs, NAT gateways and EIPs. Reconcile retained resources and continuing charges.

The November 8 cost plan estimated approximately **$0.72/hour** for Project 1 and **$0.18/hour** for Project 2 while running, before variable usage. The billed amount is not established by those figures. The recorded billing review was **November 15, 2026**.

[Cost, completed tests and outstanding work](PORTFOLIO-VALIDATION.md)
