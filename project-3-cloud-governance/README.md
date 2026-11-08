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

The governance implementation has meaningful automated checks, even though it was not deployed across six AWS accounts.

| Tested area | What the tests establish |
| --- | --- |
| **Organization guardrails** | Terraform generates explicit denies for leaving the organization, closing accounts, and disabling key audit/security services. Tests confirm a named administrator-role exception and reject wildcard role patterns. |
| **Account and audit boundaries** | Python contract tests check OU assignments, SCP attachment targets, opt-in delegated administrators, Identity Center assignments, and encrypted organization-trail configuration. |
| **Security, dashboard, and cost logic** | Python tests check handler inputs, access/configuration boundaries, stored-record behavior, and deterministic fallback paths without requiring live multi-account services. |

[Terraform policy tests](modules/scp-policies/tests/guardrails.tftest.hcl) · [Account-boundary tests](tests/test_governance_boundaries.py) · [Infrastructure tests](tests/test_governance_infrastructure.py) · [Passing offline policy CI](https://github.com/JNHolman/RSVP-Cloud-Platform/actions/runs/42508709940/job/128816887334)

These results prove **policy generation and local code/test behavior**. They do not prove live SCP enforcement, Identity Center sign-in, cross-account CloudTrail delivery, or centralized security findings.

## Engineering trade-off: why I stopped at offline validation

The available AWS account also hosted RSVP Society. Applying organization-wide controls there was not an acceptable way to experiment with policies that could affect the business.

I could have created a separate test organization with five additional member accounts. That would have made live enforcement and cross-account validation possible, but required more account administration, service spending, and eventual cleanup for a portfolio demonstration.

I kept the enterprise design and verified the parts that could be tested safely without that environment. **The benefit was protecting the business while proving the policy logic; the limitation was losing evidence of how those controls behave when AWS enforces them across accounts.**

This completes the progression from private workloads, through controlled releases, to organizational boundaries.

[Platform overview](../README.md)

[Platform overview](../README.md)
