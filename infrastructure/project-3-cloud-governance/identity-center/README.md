# RSVP IAM Identity Center

This stack requires IAM Identity Center to be enabled for the AWS Organization before Terraform runs. The configuration fails early with a clear prerequisite error if no Identity Center instance is available; it then manages permission sets and account assignments.

Permission sets:

- `CloudAdministrator` — restricted privileged access to the Security account
- `PlatformOperator` — PowerUser access to Shared Services, NonProd, and Prod
- `EngineeringReadOnly` — read-only visibility across member accounts

Group IDs are inputs so source-of-truth identity management stays outside this repository.
