# Part 3 — Cloud Governance

**A six-account AWS governance design: security policies, identity boundaries, independent audit records, and cost visibility.**

I modeled six account responsibilities: management, security, log archive, shared services, nonproduction, and production. Separate security and audit accounts keep a workload team from being solely responsible for its own oversight.

```text
Management / AWS Organizations
  ├── Security             → central security findings and incident analysis
  ├── Log archive          → audit records separated from workloads
  ├── Shared services      → common infrastructure responsibilities
  ├── Nonproduction        → development and testing workloads
  └── Production           → production workloads
```

## The guardrails defined in code

**Protect the organization and its security tools.** The service control policy (SCP) module generates a rule denying member accounts the ability to leave the organization or close their accounts. Another rule would stop ordinary workload roles from disabling CloudTrail logging, AWS Config recording, GuardDuty, or Security Hub. Terraform defines attachments to the nonproduction and production organizational units. Exceptions are limited to explicitly named administrator roles, not wildcard access.

[Actual SCP rules](modules/scp-policies/main.tf) · [Policy attachment targets](organization/scps.tf)

**Keep oversight independent of applications.** A security account is responsible for findings and a log archive account for audit records. IAM Identity Center models who can access accounts. Referencing existing accounts **does not automatically move them into organizational units**; **OU placement determines which SCPs apply**. Also, SCPs do not restrict the AWS Organizations management account.

[Account boundaries](organization/accounts.tf) · [Identity Center configuration](identity-center/main.tf)

**Make findings understandable without giving AI permission to act.** Security Hub, GuardDuty, CloudTrail, and AWS Config aggregation feed the broader security design. AWS Config aggregation only includes accounts **where Config recording is enabled**. Python handlers analyze bounded incident and cost inputs, sanitize errors, and produce deterministic fallbacks. They do not make remediation changes.

[Security analysis](security-admin/ai_incident_analyzer.py) · [FinOps analysis](finops-ai/cost_analyzer.py)

**Keep different account lifecycles separate.** Organization management, log archive, security, identity, and workload Terraform roots intentionally remain distinct. Sharing a repository does not mean those accounts should share state or deployment privileges.

## What I verified

The following controls were validated through automated tests:

| Tested area | What the tests establish |
| --- | --- |
| **Organization guardrails** | Terraform generates explicit denies for leaving the organization, closing accounts, and disabling key audit/security services. Tests confirm a named administrator-role exception and reject wildcard role patterns. |
| **Account and audit boundaries** | Python contract tests check OU assignments, SCP attachment targets, opt-in delegated administrators, Identity Center assignments, and encrypted organization-trail configuration. |
| **Security, dashboard, and cost logic** | Python tests check handler inputs, access/configuration boundaries, stored-record behavior, and deterministic fallback paths. |

[Terraform policy tests](modules/scp-policies/tests/guardrails.tftest.hcl) · [Account-boundary tests](tests/test_governance_boundaries.py) · [Infrastructure tests](tests/test_governance_infrastructure.py) · [Passing offline policy CI](https://github.com/JNHolman/RSVP-Cloud-Platform/actions/runs/42513576400/job/128831638392)

The separate Checkov IaC scan is advisory (`soft_fail: true`); passing CI does not mean every finding has been resolved.

## Engineering trade-off

The available AWS account hosted RSVP Society, so I kept experimental organization-wide controls out of that environment. An isolated six-account AWS organization could have tested real enforcement and cross-account integration, but would require additional account administration and ongoing service costs. I retained the enterprise design and validated its policies and application logic offline. **Live SCP enforcement, Identity Center sign-in, and cross-account logging/security aggregation remain unverified.**

[Platform overview](../README.md)
