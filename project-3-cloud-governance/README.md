# Project 3 — Cloud Governance

```text
AWS Organizations
 ├─ Management: policies and cost oversight
 ├─ Security: findings and incident analysis
 ├─ Log Archive: audit evidence
 └─ Workload accounts: applications and reporting
```

Terraform models SCPs, Identity Center, CloudTrail, security aggregation, dashboards, and cost analysis. Offline tests validate configuration contracts and handler behavior. **Live OU enforcement, cross-account integration, and identity flows remain unverified.**

## Evidence checklist

The [hosted CI screenshot](evidence/offline-ci.png) shows the completed Terraform policy tests. The six-account control plane has no live AWS evidence. Inspect the [policy tests](modules/scp-policies/tests/guardrails.tftest.hcl) and [governance tests](tests/).

| Area | Evidence available | Evidence still needed |
|---|---|---|
| Organization and identity | Offline Terraform tests exercise generated SCP denies and admin exceptions. Python tests inspect trust and security configuration | OU enforcement, role assumption and Identity Center assignment in member accounts |
| Security and monitoring | Local handler tests exercise finding analysis, bounded inputs, fallback and dashboard reads | Cross-account finding ingestion, central audit delivery and incident notification |
| Cost management | Local tests cover Cost Explorer input and deterministic fallback | Attributed live costs and operator review of generated recommendations |

## Operations

The six-account design is **not deployed** for this portfolio. With Terraform 1.6.6 and the project's Python test dependencies installed, run from the repository root:

```sh
(cd project-3-cloud-governance/modules/scp-policies && terraform init -backend=false && terraform validate && terraform test)
python -m pytest -q project-3-cloud-governance/tests shared/tests
```

These tests prove policy generation and local application logic. They do not prove that AWS enforced the policies across accounts.

### Proposed single-account AWS exercise

Use one short-lived portfolio deployment in us-east-1 with its own state, roles and resource names. Approval is pending. The account also hosts RSVP Society, so every write must target a portfolio resource.

| Exercise | Evidence to capture |
|---|---|
| Submit the Terraform-generated SCP documents to IAM Access Analyzer | AWS validation findings for each document. Effective OU enforcement still requires a member account. |
| Replay a labeled sample finding through a private EventBridge bus into the existing incident handler | Correlated event, Lambda analysis or fallback, stored report and notification receipt. Record the sample origin separately from real AWS delivery. |
| Invoke the existing FinOps handler with a portfolio cost-allocation tag filter | Sanitized report with the billing period and observed attribution. The current handler queries the whole account, so add and test the filter before invocation. Skip the query if the tag is unavailable. |

Budget a two-hour exercise with at most 20 Lambda invocations, ten Cost Explorer API pages and two bounded model calls. Allow $5 for AWS and $1 for the model, including teardown headroom. These are planning allowances. Remove triggers first, then retire the temporary runtime and check for retained logs and storage. OU attachments, Identity Center assignments, organization trails and delegated security administration remain enterprise architecture with offline coverage.

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
