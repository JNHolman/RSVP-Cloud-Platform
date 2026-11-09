# Project 3 — Cloud Governance

The enterprise design separates policy administration, security investigations and audit storage across accounts. I used a single account for the live investigation and tested the organization policy definitions offline.

## Live AWS exercise

A labeled critical sample arrived on a private EventBridge bus. Lambda submitted its finding metadata for analysis and applied the severity rule before writing the investigation record.

| Recorded decision | Evidence from the investigation |
|---|---|
| Model recommendation · **P3** | The model recognized a rehearsal. It asked the operator to confirm the exercise origin and check for an affected resource before attributing business impact. |
| Stored priority · **P1** | The critical severity floor overrode P3. DynamoDB recorded the investigation, and SNS delivered the notification to an encrypted SQS subscriber. |

IAM Access Analyzer returned **zero findings** for both Terraform-generated default SCP documents. Member-account enforcement remains unverified. Cost Explorer returned zero active cost-allocation tags, so the portfolio-only FinOps report was skipped.

The handler keeps the model recommendation alongside the enforced priority when the severity floor changes it. [Analysis and severity enforcement](security-admin/ai_incident_analyzer.py) · [Generated governance policies](modules/scp-policies/main.tf)

### Limits of the single-account lab

Read-only inventory in us-east-1 found no AWS Config recorder status, CloudTrail trail or GuardDuty detector. The account was unsubscribed from Security Hub CSPM. Enabling these shared services would expand collection and cost beyond the portfolio resources. The live exercise therefore starts at EventBridge with a labeled sample. The security dashboard API assumes dedicated Security and FinOps read roles to query both tables. Its behavior has offline coverage; a deployed dashboard and cross-account access remain unverified.

The six-account design uses separate state-bootstrap outputs for each backend. The example value `REPLACE_WITH_TERRAFORM_STATE_KMS_KEY_ARN` marks the owning account’s encryption key. Referencing existing accounts does not move those accounts. An account outside the target OU will not inherit that OU's SCPs. StackSets delegated administration also depends on trusted access through `ActivateOrganizationsAccess`. [Offline policy tests](modules/scp-policies/tests/guardrails.tftest.hcl) · [Hosted CI evidence](evidence/offline-ci.png)

<details><summary>Technical evidence records</summary>

[Incident and delivery record](evidence/aws-incident-exercise.json) · [Policy validation results](evidence/aws-policy-validation.json)

</details>
