# Part 3 — Cloud Governance

**What changes when a protected application becomes an organization-wide responsibility?**

The first two parts are about running and delivering workloads safely. This part explores how to apply those principles across AWS accounts, teams, and operational responsibilities.

```text
AWS Organizations + Service Control Policies
                  |
     Identity and account boundaries
                  |
  +---------------+----------------+
  |               |                |
Security       Log archive      Workloads
  |               |                |
Findings and   Audit trail      Applications
AI triage      retention        and dashboards
                  |
           Cost visibility
```

## The design

**Account boundaries.** The Terraform design separates management, security, logging, shared services, and workload responsibilities. This reduces the risk of one application account controlling its own security evidence.

**Guardrails and identity.** Service Control Policies (SCPs) describe organization-wide limits. IAM Identity Center models how people receive access. Existing AWS accounts can be referenced, but the configuration does not automatically move them into organizational units; OU placement determines which SCPs apply.

**Security and operations.** GuardDuty, Security Hub, AWS Config aggregation, CloudTrail, and central dashboards are represented in the design. Config aggregation only covers accounts **where Config recording is enabled**. The AI handlers summarize approved security, incident, and cost evidence; they don't take remediation actions.

**Cost and accountability.** The FinOps component analyzes Cost Explorer data. In keeping with the original RSVP Society lesson, the goal is to understand what infrastructure costs and whether the business justifies it.

Separate Terraform roots exist here for a technical reason: management, security, log archive, and workload accounts must not accidentally share the same state or permissions. This is intentional separation, not three more independent portfolios.

## What I verified

This is a **six-account reference design tested offline**, not a live six-account deployment.

Terraform tests exercised generated policy rules and exceptions. Python tests exercised identity/security configuration, finding analysis, dashboard behavior, cost handling, and deterministic fallbacks. That demonstrates the logic and implementation contracts—not live AWS enforcement.

There are no genuine AWS console screenshots for this part because it has not been deployed across six accounts. I have not substituted a simulated console view.

[Policy test source](modules/scp-policies/tests/guardrails.tftest.hcl) · [Governance test source](tests/)

This completes the progression: establish reliable infrastructure, deliver changes safely, then design the controls that would govern a larger environment.

[Back to the full platform](../README.md)
