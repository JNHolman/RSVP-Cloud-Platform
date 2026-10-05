# Deployment and Validation Guide

This is the deterministic order for validating and deploying the RSVP Cloud Platform. Do not collect portfolio evidence until the corresponding verification step passes.

## 1. Run repository quality gates

Push the candidate to a review branch and allow `CI - Test and Scan` to run. Automatic CI covers:

- Checkov
- Ruff
- pytest
- pip-audit
- Docker build
- Trivy HIGH/CRITICAL scan

Terraform execution is intentionally **not automatic**. If Terraform validation is needed, manually run the CI workflow with `run_terraform=true`, or run the documented Terraform commands yourself in the intended AWS/account context. Do not treat skipped Terraform validation as a pass.

## 2. Bootstrap Terraform remote state

Use an **account-local state backend** for every AWS account that will run one of these Terraform roots. This avoids silently granting member accounts access to a management-account state bucket.

Keep these backend resources dedicated to RSVP Cloud Platform. Do not reuse the RSVP Society state bucket, lock table, KMS resources, or other business infrastructure.

At minimum, bootstrap `infrastructure/bootstrap-state` with local state in the management, Security, Log Archive, and workload/Prod accounts used by the deployment. Use a globally unique `state_bucket_name` in each account. Record these outputs for each account:

- `state_bucket_name`
- `lock_table_name`
- `state_kms_key_arn`

Use the backend belonging to the account where that Terraform root is executed:

- management account: `organization`, `audit-trail`, `finops-ai`, and `identity-center`
- Security account: `security-admin`
- Log Archive account: `log-archive`
- workload/Prod account: `workload` and workload infrastructure deployed there

Each Project 3 root includes a `backend.hcl.example`. Copy it to an untracked local `backend.hcl`, replace both the bucket placeholder and `REPLACE_WITH_TERRAFORM_STATE_KMS_KEY_ARN` with that account's state-bootstrap outputs, and initialize with `terraform init -backend-config=backend.hcl`. If you intentionally centralize state in one account instead, configure and review the required cross-account S3/KMS/backend-role permissions first; this repository does not grant them implicitly.

## 3. Bootstrap Project 2 delivery

Apply `infrastructure/project-2-ecs-cicd/bootstrap-delivery` once per AWS account. It creates:

- one GitHub Actions OIDC provider
- dev/stage/prod ECR repositories
- environment-scoped GitHub deployment roles

Copy each role ARN into the matching GitHub Environment variable `AWS_DEPLOY_ROLE_ARN`. If Project 2 uses non-default Terraform values for `aws_region` or `project_name`, also set matching GitHub Environment variables `AWS_REGION` and `PROJECT_NAME`; otherwise the workflows use `us-east-1` and `rsvp-project2`.

Before treating the `prod` OIDC role as production-ready, configure GitHub Environment protection rules for `prod`: restrict deployment branches/tags to the approved release source (for example `main` or explicit release tags) and require a deployment approval where the repository plan supports it. The AWS trust policy intentionally scopes the OIDC subject to the repository plus GitHub Environment; GitHub Environment protection is therefore part of the production authorization boundary, not an optional cosmetic setting. Apply comparable branch/tag restrictions to `stage` when it is used as a release gate.

## 4. Push the first immutable container image

Run **ECS Project 2 - Bootstrap First Image** for the target environment.

Record the exact Git-SHA image URI that the workflow prints. Put that URI in the target environment's local `terraform.tfvars` as `container_image`. Never replace it with `:latest`.

## 5. Deploy Project 1 infrastructure

Prepare the target environment variables with:

- Route53 hosted-zone ID
- application DNS name
- Secrets Manager ARN containing the OpenAI API key
- optional alert email

For Project 1, copy the target environment's `backend.hcl.example` to an untracked `backend.hcl`, replace both the state-bucket placeholder and `REPLACE_WITH_TERRAFORM_STATE_KMS_KEY_ARN` with the outputs from the state bootstrap, initialize with `terraform init -backend-config=environments/<environment>/backend.hcl`, review `terraform plan`, then apply. Verify private EC2 placement, HTTPS, WAF, Multi-AZ RDS, managed database secret, backups, alarms, and dashboard.

## 6. Deploy Project 2 ECS runtime

For Project 2, copy the target environment's `backend.hcl.example` to an untracked `backend.hcl`, replace the state-bucket and state-KMS-key placeholders with the outputs from the state bootstrap, and initialize the runtime stack with that backend config. Use the immutable first-image URI from step 4 plus the Route53 zone/domain for the target environment.

After apply, verify:

- at least two healthy tasks
- tasks span Availability Zones
- no public task IPs
- HTTPS `/health` returns `status=ok`
- autoscaling target exists
- deployment circuit breaker is enabled

Set GitHub Environment variable `SERVICE_URL` to the HTTPS service URL.

## 7. Deploy governance foundation

If `create_member_accounts=false`, the organization stack only references the supplied account IDs; it does not move those accounts. Before relying on OU-level SCPs, verify that the existing Security, Log Archive, Shared Services, NonProd, and Prod accounts are already in the intended OUs, and deliberately move/import them where required. An account outside the target OU will not inherit that OU's SCPs.

Security-control SCP exceptions are empty by default. If a break-glass or automation role must be exempted, supply only its explicit account-scoped IAM role ARN in `protected_admin_role_patterns`; wildcard account IDs are rejected.

If StackSets delegated administration is enabled, activate CloudFormation StackSets trusted access (`ActivateOrganizationsAccess`) before enabling that delegated-admin path.

Deploy the Project 3 stacks in dependency order:

1. `organization` from the Organizations management account
2. `log-archive` in the Log Archive account
3. `audit-trail` from the management account using the Log Archive bucket/KMS outputs
4. `security-admin` in the delegated Security account
5. `finops-ai` in the management/payer account
6. `identity-center` from the management account
7. `workload` in the workload/prod account

For the dashboard cross-account path, configure Security and FinOps with the workload account ID and deterministic dashboard role name before deploying the workload stack. Then pass the resulting read-role ARNs to the workload stack.

## 8. Validate controlled application deployment

Run **ECS Project 2 - Controlled Deploy** with a normal code revision. Verify:

- build/test/scan succeeds
- SHA image is pushed
- new task definition becomes active
- post-deployment HTTPS smoke test succeeds

Then perform one safe rollback exercise by deploying a deliberately unhealthy test revision and verify the workflow returns the service to the previous task definition.

**Task-definition ownership:** Terraform registers the infrastructure/security configuration baseline and tags it `ConfigurationSource=TerraformBaseline`. The ECS service intentionally ignores `task_definition` drift so a later Terraform apply cannot roll back a GitHub-deployed application release. Therefore, after any Terraform change that modifies the ECS task definition, run **Controlled Deploy** before treating that configuration change as active. The workflow clones the latest Terraform baseline, replaces only the release image/version, and promotes that revision to the service.

## 9. Validate operations and recovery

At minimum, prove:

- CloudWatch dashboard and alarm transition
- ECS rollback
- RDS restore exercise
- GuardDuty/Security Hub signal path
- authenticated API behavior
- WAF association
- AI incident analysis with confidence/evidence
- Cost Explorer-backed FinOps report

Treat RTO/RPO values as targets until the recovery exercises produce measured results.

## 10. Evidence and cleanup

Capture only a small set of high-value evidence: architecture, successful CI/security gates, private ECS placement, healthy service/rollback, RDS recovery, CloudWatch alarms, GuardDuty/Security Hub, and one AI-analysis example. Redact account identifiers or secrets where appropriate.

After evidence is captured, destroy expendable demo workload resources that are not intended to remain running. Do not expect an unrestricted `terraform destroy` to remove the protected remote-state, centralized-audit, or Project 1 recovery KMS resources. Those resources use intentional Terraform destruction guards. For a complete teardown, first confirm that the dependent Terraform state, audit data, RDS snapshots, and AWS Backup recovery points no longer need to be recoverable, then deliberately remove the relevant guard as part of the teardown change.
