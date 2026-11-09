# Project 3 — Cloud Governance

```text
AWS Organizations
 ├─ Management: policies and cost oversight
 ├─ Security: findings and incident analysis
 ├─ Log Archive: audit evidence
 └─ Workload accounts: applications and reporting
```

Terraform models SCPs, Identity Center, CloudTrail, security aggregation, dashboards, and cost analysis. Offline tests validate configuration contracts and handler behavior. **Live OU enforcement, cross-account integration, and identity flows remain unverified.**

## Live AWS exercise

A private EventBridge bus delivered a labeled sample critical finding to the governance Lambda. The model recognized the rehearsal and proposed **P3**. The handler enforced the configured critical severity floor of **P1**, stored the report in DynamoDB, and published a notification through SNS. An encrypted SQS subscriber received it. The sample exercised the downstream pipeline. Live Security Hub detection and cross-account aggregation remain unverified.

IAM Access Analyzer returned **zero findings** for both Terraform-generated default SCP documents. Member-account enforcement remains unverified. Cost Explorer returned zero active cost-allocation tags, so the portfolio-only FinOps report was skipped.

[Incident and delivery record](evidence/aws-incident-exercise.json) · [Policy validation results](evidence/aws-policy-validation.json)

## Evidence checklist

The [hosted CI screenshot](evidence/offline-ci.png) shows the completed Terraform policy tests. The six-account control plane has no live AWS evidence. Inspect the [policy tests](modules/scp-policies/tests/guardrails.tftest.hcl) and [governance tests](tests/).

| Area | Evidence available | Evidence still needed |
|---|---|---|
| Organization and identity | Offline Terraform tests exercise generated SCP denies and admin exceptions. Python tests inspect trust and security configuration | OU enforcement, role assumption and Identity Center assignment in member accounts |
| Security and monitoring | Local handler tests exercise finding analysis, bounded inputs, fallback and dashboard reads | Cross-account finding ingestion, central audit delivery |
| Cost management | Local tests cover Cost Explorer input and deterministic fallback | Attributed live costs and operator review of generated recommendations |

### Limits of the single-account lab

Read-only inventory in us-east-1 found no AWS Config recorder status, CloudTrail trail or GuardDuty detector. The account was unsubscribed from Security Hub CSPM. Enabling these shared services would expand collection and cost beyond the portfolio resources. The live exercise therefore starts at EventBridge with a labeled sample. The security dashboard API assumes dedicated Security and FinOps read roles to query both tables. Its behavior has offline coverage; a deployed dashboard and cross-account access remain unverified.

## Operations

The six-account design is **not deployed** for this portfolio. With Terraform 1.6.6 and the project's Python test dependencies installed, run from the repository root:

```sh
(cd project-3-cloud-governance/modules/scp-policies && terraform init -backend=false && terraform validate && terraform test)
python -m pytest -q project-3-cloud-governance/tests shared/tests
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

[Platform overview](../README.md) · [Shared state, DNS, costs and teardown](../shared/OPERATIONS.md)
