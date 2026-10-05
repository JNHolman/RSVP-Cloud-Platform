# RSVP Enterprise Organization Bootstrap

This stack runs **only in the AWS Organizations management account**. It replaces the former metadata-only organization placeholder with deployable governance code.

It creates:

- Security, Infrastructure, Workloads, NonProd, and Prod OUs
- optional creation of member accounts, or references to pre-existing account IDs
- root-level SCP guardrails that prevent member accounts from leaving the organization or closing, plus workload protections for security/logging controls
- GuardDuty and Security Hub delegated administration to the Security account
- AWS Config delegated administration to the Security account
- optional CloudFormation StackSets delegated administration to Shared Services **after** StackSets trusted access is activated through CloudFormation
- preservation of IAM Identity Center trusted access (`sso.amazonaws.com`); the Identity Center instance must still be enabled through IAM Identity Center before the Identity Center Terraform root runs

## Deployment order

1. Bootstrap the Terraform remote-state backend.
2. Apply this organization stack from the management account. Pre-existing account IDs are referenced only; this stack does not move those accounts into its OUs.
3. Record the `account_ids` output.
4. If service-managed StackSets are required, activate AWS Organizations trusted access from CloudFormation StackSets (console or `ActivateOrganizationsAccess`). This CloudFormation-specific step creates the required service-linked role. Then set `stacksets_trusted_access_activated = true` and re-apply this stack to preserve the trusted-access principal and register Shared Services as the StackSets delegated administrator.
5. Apply `../security-admin` while authenticated to the delegated Security account.
6. Deploy logging and workload stacks into their respective member accounts.

The management account should contain governance resources only, not application workloads.
