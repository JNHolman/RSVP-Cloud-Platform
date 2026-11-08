# Part 3 — Cloud Governance

**The final design question: how do you maintain security, identity, and audit boundaries when more than one account or team is involved?**

I modeled a six-account AWS organization, separating management, security, log archive, shared services, nonproduction, and production. These are responsibilities that should not all live in the same application account.

```text
Management / AWS Organizations
  ├── Security             → central security findings and incident analysis
  ├── Log archive          → audit records separated from workloads
  ├── Shared services      → common infrastructure responsibilities
  ├── Nonproduction        → development and testing workloads
  └── Production           → production workloads
```

## What the implementation enforces by design

**Protect the organization and its security tools.** The SCP module denies member accounts permission to leave the organization or close their accounts. A second policy blocks ordinary workload principals from stopping or altering CloudTrail logging, AWS Config recording, GuardDuty, and Security Hub. It is attached to the nonproduction and production organizational units, with optional, explicitly named administrator-role exceptions—not broad wildcard exemptions.

[Actual SCP rules](modules/scp-policies/main.tf) · [Policy attachment targets](organization/scps.tf)

**Put independent evidence outside the workload account.** The design separates a security account for centralized findings and a log archive account for audit records. IAM Identity Center models human access. Referencing existing accounts **does not automatically move them into organizational units**; **OU placement determines which SCPs apply**. Also, SCPs do not restrict the AWS Organizations management account.

[Account boundaries](organization/accounts.tf) · [Identity Center configuration](identity-center/main.tf)

**Make findings understandable without giving AI permission to act.** Security Hub, GuardDuty, CloudTrail, and AWS Config aggregation feed the broader security design. AWS Config aggregation only includes accounts **where Config recording is enabled**. Python handlers analyze bounded incident and cost inputs, sanitize errors, and produce deterministic fallbacks. They do not make remediation changes.

[Security analysis](security-admin/ai_incident_analyzer.py) · [FinOps analysis](finops-ai/cost_analyzer.py)

**Keep different account lifecycles separate.** Organization management, log archive, security, identity, and workload Terraform roots intentionally remain distinct. Sharing a repository does not mean those accounts should share state or deployment privileges.

## What was tested, and what wasn't

This is an **offline-tested six-account reference design**, not a deployed AWS organization. Terraform tests checked policy generation and role exceptions; Python tests exercised infrastructure contracts, security analysis, dashboard reads, cost handling, and fallback responses.

That proves the implementation and test behavior locally. It **does not** prove live SCP enforcement, Identity Center access, cross-account audit delivery, or security finding aggregation. There is no live six-account evidence to claim otherwise.

[Terraform policy tests](modules/scp-policies/tests/guardrails.tftest.hcl) · [Governance tests](tests/)

This completes the design progression: private application infrastructure, repeatable delivery, and organizational controls around both.

[Platform overview](../README.md)
