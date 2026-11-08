# Part 3 — Cloud Governance

**A reference design for applying the same security and operational discipline across an AWS organization.**

A single workload can use private networks, encryption, monitoring, and careful deployment controls. As the number of teams and accounts grows, the harder question becomes who is allowed to change those controls—and who can independently see what happened.

This part explores that question with Terraform and Python. It is an **offline-tested six-account design**, not a running six-account AWS deployment.

```text
Management / AWS Organizations
  ├── Security account          → central findings and incident analysis
  ├── Log archive account       → separated audit evidence
  ├── Shared services account   → shared infrastructure responsibilities
  ├── Nonproduction account     → workload testing boundary
  └── Production account        → protected workload boundary
```

## The engineering work

**Separate duties across accounts.** Organizations and service control policies (SCPs) model limits on what member accounts can change. IAM Identity Center defines human access. Security and log archive responsibilities sit outside the application accounts so audit and security controls don't depend solely on the teams being monitored.

**Apply guardrails where they matter.** Terraform models organizational-unit policy attachments and defined administrator exceptions. Referencing existing accounts **does not automatically move them into organizational units**; **OU placement determines which SCPs apply**. These are configuration and enforcement boundaries, not merely labels.

**Centralize signals without handing AI the controls.** GuardDuty, Security Hub, CloudTrail, and AWS Config aggregation are included in the design, alongside incident analysis and dashboards. Config aggregation covers accounts only **where Config recording is enabled**. Analysis functions have bounded inputs and fallback handling; they report findings rather than automatically changing resources.

**Make costs visible.** FinOps analysis works with Cost Explorer data. This closes the loop on the original RSVP Society lesson: enterprise infrastructure should be justified by its workload and operating cost, not just by how much can be provisioned.

Separate Terraform roots keep management, security, archive, and workload deployments in their appropriate state and permission boundaries. Their separation protects those responsibilities while the work remains one coherent platform design.

## What was validated

Terraform tests exercised policy generation and SCP exceptions. Python tests covered configuration contracts, security/incident handling, dashboard reads, cost analysis, and fallback behavior.

These checks demonstrate that the **policies and application logic are implemented and tested offline**. They do **not** prove that a live AWS organization enforced SCPs, Identity Center grants, cross-account audit delivery, or security aggregation. There is no live six-account console evidence to claim.

[Policy test source](modules/scp-policies/tests/guardrails.tftest.hcl) · [Governance test suite](tests/)

Foundation established the workload controls. Delivery applied them to releases. Governance shows how I would extend them across an organization.

[Platform overview](../README.md)
