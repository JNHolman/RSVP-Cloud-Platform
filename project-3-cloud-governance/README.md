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

## Why I tested this part offline

The AWS account available for the portfolio was also hosting RSVP Society. The six-account model required five additional accounts and centralized services, so deploying it into that environment would have introduced cost and risks to the business for no immediate business benefit.

I used Terraform tests to check the actual SCP rules and administrator exceptions, plus Python tests for configuration, incident analysis, dashboards, and cost handling. Those tests verify the implementation **without claiming that the policies were enforced across live AWS accounts**.

[Terraform policy tests](modules/scp-policies/tests/guardrails.tftest.hcl) · [Governance tests](tests/)

Together with the first two parts, this shows how I approached the same security and operational problems from workload design through organization-wide controls.

[Platform overview](../README.md)
