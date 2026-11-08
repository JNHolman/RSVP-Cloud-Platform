# AWS exercise safeguards and resource custody

The Cloud Platform exercises used temporary resources in an AWS account that also supported [RSVP Society](https://github.com/JNHolman/rsvp-society). The governing rule was to **prove engineering behavior without changing the business infrastructure**. This reference preserves the ownership, recovery, and cleanup decisions behind that work. It is not a live inventory or an instruction to redeploy the exercises.

## Establish ownership before making changes

- **Identify the environment.** Verify AWS account, role, region, and the expected portfolio resource prefix. The November 2026 exercises used `us-east-1`. Do not assume the shell's default profile or workspace is the correct one.
- **Reconcile Terraform state with AWS.** Record the backend bucket, state key, workspace, state lineage, and resource ARNs; compare them with direct service inventory. An existing resource with no corresponding trusted state or an unexpected backend is a **stop condition**, not permission to import, recreate, or destroy it. Keep raw plans, state, credentials, and secrets out of Git.
- **Keep the business outside every plan.** RSVP Society's application resources, data stores, IAM roles, buckets, state, and live DNS are not owned by this portfolio. Review proposed replacements and changes to IAM, DNS, networking, databases, and encryption keys individually.
- **Use the actual plan reviewer.** [`review-portfolio-plan.py`](review-portfolio-plan.py) checks the Project 1/2 first-deployment inputs, DNS scope, and attempts to change existing resources. It requires an independently verified child-zone ID and is **not approval** for an apply, update, or teardown. The [tests](tests/test_portfolio_plan_review.py) demonstrate its allowed and rejected plans.

**Historical ownership issue:** On November 7, 2026, a legacy `rsvp-dev-asg` had failed scaling activities and unresolved Terraform ownership. Its name and tags were insufficient evidence to adopt it. The November 8 portfolio-dev exercise was separate. This is a dated observation, not a claim about the group's current state.

## Protect DNS and deployment identities

The portfolio used a delegated `cloud.rsvpsociety.com` child zone, with `dev.cloud.rsvpsociety.com` for EC2 and `ecs.cloud.rsvpsociety.com` for Fargate. Before any authorized change, verify parent delegation, authoritative child records, zone ownership, and ACM validation records. **Do not modify the parent nameservers or RSVP Society's apex, www, or API records.** Delete only the workload DNS records owned by the exercise; retiring the child delegation is a separate decision.

Terraform roots require their own correct backend and keys from [shared state bootstrap](bootstrap-state/). Local `backend.hcl` and variable values must remain untracked. The GitHub OIDC identity provider is account-wide: verify ownership before bootstrap rather than taking over an existing provider. Deployment-role trust must match the intended repository and GitHub Environment; production use additionally depends on restricted release sources and required approvals.

## Keep recovery artifacts recoverable

Project 1's database encryption key and protected recovery resources have Terraform `prevent_destroy` safeguards. A restored snapshot is only useful while its KMS key, permissions, and recovery credentials remain available. Retain these dependencies together with snapshots, backup recovery points, and encrypted incident evidence until the owner has approved an expiry and retirement decision.

An unrestricted whole-root `terraform destroy`, deletion of state to bypass ownership, or removal of a destruction guard is **not** an acceptable cleanup method. Review disposable resources by address and ARN, remove only the scoped demo workload, and verify directly that EC2/ASG, ECS tasks, databases (including temporary restores), ALBs, NAT gateways, and EIPs are gone. Remove ECS runtime resources before its delivery bootstrap. Preserve shared Terraform state, relevant backups, log/evidence buckets, required KMS keys, and the account-owned OIDC provider.

Use resource ARNs **and** direct AWS inventory; tags alone missed resources in the historical preflight. Inventory retained artifacts and assign an owner and retention decision. Confirm running charges after cleanup rather than assuming that a successful Terraform command ended all billing.

## Dated evidence and costs

The [Foundation exercise](../project-1-cloud-foundation/evidence/2026-11-08.md) and [ECS exercise](../project-2-ecs-cicd/evidence/2026-11-08.md) record what was running, measured, removed, and retained on November 8, 2026. Their **planning** estimates were about **$0.72/hour** for the complete foundation stack and **$0.18/hour** for the ECS runtime, excluding some usage and long-lived retention charges. Actual incremental charges were not established; the cost-allocation tag was inactive. The original record scheduled a billing and retention review for November 15, 2026, not confirmation of its completion.

The detailed historical preflight, cost worksheet, validation matrix, and teardown notes remain available in the [original operations record](https://github.com/JNHolman/RSVP-Cloud-Platform/blob/f69ffeae33207d97e358e91e91e4edf9b48c96b6/shared/OPERATIONS.md). The dated exercise evidence is the source for test results, not this safety reference.
