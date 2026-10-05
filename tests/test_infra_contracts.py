from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text()


def test_project1_observability_contract():
    alb = read("infrastructure/project-1-cloud-platform/alb.tf")
    logs = read("infrastructure/project-1-cloud-platform/observability-security.tf")
    app_logs = read("infrastructure/project-1-cloud-platform/ai-logs.tf")

    assert "access_logs {" in alb
    assert 'enable_deletion_protection = var.environment == "prod"' in alb
    assert "drop_invalid_header_fields = true" in alb
    assert 'resource "aws_flow_log" "vpc"' in logs
    assert 'resource "aws_wafv2_web_acl_logging_configuration" "app"' in logs
    assert 'resource "aws_cloudwatch_log_group" "rds_exports"' in logs
    rds = read("infrastructure/project-1-cloud-platform/rds.tf")
    assert "aws_cloudwatch_log_group.rds_exports" in rds
    assert "kms_key_id        = aws_kms_key.observability.arn" in app_logs


def test_project2_observability_contract():
    alb = read("infrastructure/project-2-ecs-cicd/terraform/alb.tf")
    logs = read("infrastructure/project-2-ecs-cicd/terraform/observability-security.tf")
    ecs_logs = read("infrastructure/project-2-ecs-cicd/terraform/cloudwatch.tf")

    assert "access_logs {" in alb
    assert 'enable_deletion_protection = var.environment == "prod"' in alb
    assert "drop_invalid_header_fields = true" in alb
    assert 'resource "aws_flow_log" "vpc"' in logs
    assert 'resource "aws_wafv2_web_acl_logging_configuration" "app"' in logs
    assert "kms_key_id        = aws_kms_key.observability.arn" in ecs_logs


def test_workloads_do_not_receive_public_ips():
    infrastructure = "\n".join(
        path.read_text() for path in (ROOT / "infrastructure").rglob("*.tf")
    )
    assert "assign_public_ip = true" not in infrastructure
    assert "associate_public_ip_address = true" not in infrastructure


def test_ec2_requires_imdsv2_detailed_monitoring_and_encrypted_root_volume():
    ec2 = read("infrastructure/project-1-cloud-platform/ec2.tf")
    assert 'http_tokens                 = "required"' in ec2
    assert "http_put_response_hop_limit = 1" in ec2
    assert "monitoring {" in ec2
    assert "enabled = true" in ec2
    assert "encrypted             = true" in ec2


def test_github_oidc_and_deploy_rollback_contract():
    oidc = read("infrastructure/project-2-ecs-cicd/bootstrap-delivery/main.tf")
    workflow = read(".github/workflows/ecs-project2-deploy.yml")

    assert "thumbprint_list" in oidc
    assert "steps.deploy.outcome == 'failure' || steps.smoke.outcome == 'failure'" in workflow
    assert '--task-definition "$PREVIOUS_TASK_DEF"' in workflow
    assert '--task-definition "$ECS_TASK_DEFINITION_FAMILY"' not in workflow
    assert 'case "$SERVICE_URL" in' in workflow
    assert "curl --proto '=https' --tlsv1.2" in workflow


def test_organization_existing_accounts_are_reference_only():
    variables = read("infrastructure/project-3-cloud-governance/organization/variables.tf")
    prerequisites = read("infrastructure/project-3-cloud-governance/organization/prerequisites.tf")
    deployment = read("docs/DEPLOYMENT.md")

    assert "does not move existing accounts between OUs" in variables
    assert "does not move those accounts" in deployment
    assert 'resource "terraform_data" "delegated_admin_prerequisites"' in prerequisites


def test_governance_lambda_logs_are_explicit_and_encrypted():
    security = read("infrastructure/project-3-cloud-governance/security-admin/observability.tf")
    finops = read("infrastructure/project-3-cloud-governance/finops-ai/observability.tf")
    workload = read("infrastructure/project-3-cloud-governance/workload/observability.tf")

    for content in (security, finops, workload):
        assert 'resource "aws_kms_key" "observability"' in content
        assert "kms_key_id        = aws_kms_key.observability.arn" in content


def test_state_bucket_is_protected_and_owner_enforced():
    state = read("infrastructure/bootstrap-state/main.tf")
    assert "prevent_destroy = true" in state
    assert 'object_ownership = "BucketOwnerEnforced"' in state
    assert "block_public_policy     = true" in state
    assert 'sse_algorithm     = "aws:kms"' in state


def test_identity_center_fails_with_explicit_prerequisite():
    identity = read("infrastructure/project-3-cloud-governance/identity-center/main.tf")
    assert "identity_center_instances" in identity
    assert "length(local.identity_center_instances) == 1" in identity
    assert "IAM Identity Center must be enabled" in identity
    assert "tolist(data.aws_ssoadmin_instances.this.arns)[0]" not in identity


def test_project1_two_az_contract_and_instance_refresh():
    variables = read("infrastructure/project-1-cloud-platform/variables.tf")
    ec2 = read("infrastructure/project-1-cloud-platform/ec2.tf")
    assert "length(var.public_subnet_cidrs) == 2" in variables
    assert "length(var.private_subnet_cidrs) == 2" in variables
    assert "instance_refresh {" in ec2
    assert 'triggers = ["launch_template"]' in ec2


def test_alarm_topics_use_service_compatible_customer_managed_kms():
    p1_topic = read("infrastructure/project-1-cloud-platform/monitoring.tf")
    p2_topic = read("infrastructure/project-2-ecs-cicd/terraform/observability.tf")
    p1_key = read("infrastructure/project-1-cloud-platform/observability-security.tf")
    p2_key = read("infrastructure/project-2-ecs-cicd/terraform/observability-security.tf")
    p1_iam = read("infrastructure/project-1-cloud-platform/iam.tf")

    assert 'alias/aws/sns' not in p1_topic + p2_topic
    assert 'kms_master_key_id = aws_kms_key.observability.arn' in p1_topic
    assert 'kms_master_key_id = aws_kms_key.observability.arn' in p2_topic
    for key in (p1_key, p2_key):
        assert 'Principal = { Service = "sns.amazonaws.com" }' in key
        assert 'Principal = { Service = "cloudwatch.amazonaws.com" }' in key
    assert 'Sid = "UseAlertTopicKmsKey"' in p1_iam


def test_organization_enables_cloudtrail_trusted_access():
    organization = read("infrastructure/project-3-cloud-governance/organization/organization.tf")
    assert '"cloudtrail.amazonaws.com"' in organization

def test_organization_preserves_identity_center_trusted_access():
    organization = read("infrastructure/project-3-cloud-governance/organization/organization.tf")
    assert '"sso.amazonaws.com"' in organization


def test_governance_dynamodb_uses_customer_managed_kms():
    security = read("infrastructure/project-3-cloud-governance/security-admin/ai-operations.tf")
    finops = read("infrastructure/project-3-cloud-governance/finops-ai/main.tf")

    # The tables remain encrypted by the customer-managed observability keys.
    for content in (security, finops):
        assert "kms_key_arn = aws_kms_key.observability.arn" in content

    # DynamoDB performs table encryption transparently and creates/uses its own
    # KMS grants. Runtime application roles must not administer those grants.
    for content in (security, finops):
        assert '"kms:CreateGrant"' not in content
        assert 'StringLike = { "kms:ViaService" = "dynamodb.*.amazonaws.com" }' not in content


def test_all_lambda_functions_use_customer_kms_and_xray():
    files = {
        "p1": read("infrastructure/project-1-cloud-platform/ai-logs.tf"),
        "security": read("infrastructure/project-3-cloud-governance/security-admin/ai-operations.tf"),
        "finops": read("infrastructure/project-3-cloud-governance/finops-ai/main.tf"),
        "dashboard": read("infrastructure/project-3-cloud-governance/workload/api.tf"),
    }
    for content in files.values():
        assert 'kms_key_arn                    = aws_kms_key.observability.arn' in content
        assert 'tracing_config {' in content
        assert 'mode = "Active"' in content

    attachments = "\n".join([
        read("infrastructure/project-1-cloud-platform/iam.tf"),
        files["security"],
        files["finops"],
        read("infrastructure/project-3-cloud-governance/workload/api_iam.tf"),
    ])
    assert attachments.count("AWSXRayDaemonWriteAccess") >= 4


def test_release_validator_cleans_generated_python_artifacts():
    validator = read("scripts/validate-release.sh")
    assert "cleanup_generated()" in validator
    assert "trap cleanup_generated EXIT" in validator
    assert "__pycache__" in validator
    assert ".pytest_cache" in validator


def test_dashboard_data_model_returns_recent_records_deterministically():
    security = read("infrastructure/project-3-cloud-governance/security-admin/ai-operations.tf")
    finops = read("infrastructure/project-3-cloud-governance/finops-ai/main.tf")
    dashboard = read("infrastructure/project-3-cloud-governance/workload/dashboard_api.py")
    sec_handler = read("infrastructure/project-3-cloud-governance/security-admin/ai_incident_analyzer.py")
    fin_handler = read("infrastructure/project-3-cloud-governance/finops-ai/cost_analyzer.py")

    assert 'name            = "by_updated_at"' in security
    assert 'range_key       = "updated_at"' in security
    assert 'name            = "by_generated_at"' in finops
    assert 'range_key       = "generated_at"' in finops
    assert '"${aws_dynamodb_table.ai_incidents.arn}/index/*"' in security
    assert '"${aws_dynamodb_table.cost_reports.arn}/index/*"' in finops
    assert '"record_type": {"S": "incident"}' in sec_handler
    assert '"record_type": {"S": "weekly_cost"}' in fin_handler
    assert "ScanIndexForward=False" in dashboard
    assert ".scan(" not in dashboard


def test_workload_cross_account_inputs_are_validated():
    variables = read("infrastructure/project-3-cloud-governance/workload/variables.tf")
    assert variables.count("must be a valid IAM role ARN") == 2
    assert "ai_incidents_table_name must not be empty" in variables
    assert "ai_cost_summaries_table_name must not be empty" in variables


def test_public_subnets_do_not_auto_assign_public_ips():
    p1 = read("infrastructure/project-1-cloud-platform/vpc.tf")
    p2 = read("infrastructure/project-2-ecs-cicd/terraform/vpc.tf")
    assert "map_public_ip_on_launch = true" not in p1 + p2


def test_rds_enhanced_monitoring_and_iam_auth_are_enabled():
    rds = read("infrastructure/project-1-cloud-platform/rds.tf")
    assert 'resource "aws_iam_role" "rds_monitoring"' in rds
    assert 'monitoring_interval = 60' in rds
    assert 'monitoring_role_arn = aws_iam_role.rds_monitoring.arn' in rds
    assert 'iam_database_authentication_enabled = true' in rds


def test_albs_enable_desync_mitigation():
    p1 = read("infrastructure/project-1-cloud-platform/alb.tf")
    p2 = read("infrastructure/project-2-ecs-cicd/terraform/alb.tf")
    for content in (p1, p2):
        assert 'desync_mitigation_mode     = "defensive"' in content


def test_s3_lifecycle_and_acl_hardening_contracts():
    ai = read("infrastructure/project-1-cloud-platform/ai-logs.tf")
    p1_logs = read("infrastructure/project-1-cloud-platform/observability-security.tf")
    p2_logs = read("infrastructure/project-2-ecs-cicd/terraform/observability-security.tf")
    audit = read("infrastructure/project-3-cloud-governance/log-archive/main.tf")
    state = read("infrastructure/bootstrap-state/main.tf")
    assert 'object_ownership = "BucketOwnerEnforced"' in ai
    for content in (ai, p1_logs, p2_logs, audit, state):
        assert 'days_after_initiation = 7' in content
    assert 'resource "aws_s3_bucket_lifecycle_configuration" "terraform_state"' in state
    assert 'noncurrent_days = 365' in state


def test_project2_ecr_uses_customer_managed_kms_encryption():
    bootstrap = read("infrastructure/project-2-ecs-cicd/bootstrap-delivery/main.tf")
    assert 'resource "aws_kms_key" "ecr"' in bootstrap
    assert 'encryption_type = "KMS"' in bootstrap
    assert 'kms_key         = aws_kms_key.ecr.arn' in bootstrap
    assert 'encryption_type = "AES256"' not in bootstrap


def test_production_backup_vault_uses_reversible_governance_lock():
    backup = read("infrastructure/project-1-cloud-platform/backup.tf")
    assert 'resource "aws_backup_vault_lock_configuration" "production"' in backup
    assert 'count = var.environment == "prod" ? 1 : 0' in backup
    assert 'min_retention_days = 7' in backup
    assert 'max_retention_days = 35' in backup
    assert not any(line.lstrip().startswith('changeable_for_days') for line in backup.splitlines())


def test_project1_ai_dynamodb_kms_permissions_are_runtime_compatible():
    iam = read("infrastructure/project-1-cloud-platform/iam.tf")
    # DynamoDB table encryption is transparent to the application runtime.
    # The Lambda only needs PutItem; it must not administer DynamoDB KMS grants.
    assert 'Sid = "DynamoWriteMetadata"' in iam
    assert 'Action = ["dynamodb:PutItem"]' in iam
    assert 'Sid = "UseDynamoDbEvidenceKmsKey"' not in iam
    assert '"kms:CreateGrant"' not in iam


def test_remote_state_locking_is_protected_and_customer_encrypted():
    state = read("infrastructure/bootstrap-state/main.tf")
    assert "deletion_protection_enabled = true" in state
    assert "kms_key_arn = aws_kms_key.terraform_state.arn" in state
    assert state.count("prevent_destroy = true") >= 3


def test_log_archive_has_destruction_safeguards():
    archive = read("infrastructure/project-3-cloud-governance/log-archive/main.tf")
    assert archive.count("prevent_destroy = true") >= 2


def _terraform_roots():
    roots = set()
    for path in (ROOT / "infrastructure").rglob("*.tf"):
        roots.add(path.parent)
    return sorted(roots)


def test_no_duplicate_terraform_resource_or_data_declarations():
    import re

    declaration = re.compile(r'^\s*(resource|data)\s+"([^"]+)"\s+"([^"]+)"', re.MULTILINE)
    for stack in _terraform_roots():
        seen = set()
        for path in sorted(stack.glob("*.tf")):
            for kind, resource_type, name in declaration.findall(path.read_text()):
                key = (kind, resource_type, name)
                assert key not in seen, f"duplicate Terraform declaration in {stack}: {key}"
                seen.add(key)


def test_terraform_provider_references_resolve_within_each_root():
    import re

    declaration = re.compile(r'^\s*(resource|data)\s+"([^"]+)"\s+"([^"]+)"', re.MULTILINE)
    data_ref = re.compile(r'\bdata\.((?:aws|archive|tls)_[a-z0-9_]+)\.([A-Za-z0-9_]+)\b')
    resource_ref = re.compile(r'(?<!data\.)\b((?:aws_[a-z0-9_]+|terraform_data))\.([A-Za-z0-9_]+)\b')

    for stack in _terraform_roots():
        text = "\n".join(path.read_text() for path in sorted(stack.glob("*.tf")))
        resources = set()
        data_sources = set()
        for kind, resource_type, name in declaration.findall(text):
            (data_sources if kind == "data" else resources).add((resource_type, name))

        missing_data = sorted(set(data_ref.findall(text)) - data_sources)
        missing_resources = sorted(set(resource_ref.findall(text)) - resources)
        assert not missing_data, f"unresolved Terraform data references in {stack}: {missing_data}"
        assert not missing_resources, f"unresolved Terraform resource references in {stack}: {missing_resources}"


def test_project3_has_explicit_account_local_backend_examples():
    base = ROOT / "infrastructure/project-3-cloud-governance"
    stacks = ["organization", "audit-trail", "finops-ai", "identity-center", "security-admin", "log-archive", "workload"]
    for stack in stacks:
        example = (base / stack / "backend.hcl.example").read_text()
        assert "REPLACE_WITH_ACCOUNT_LOCAL_TERRAFORM_STATE_BUCKET" in example
        assert 'dynamodb_table = \"rsvp-cloud-platform-terraform-locks\"' in example


def test_cloud_platform_state_names_are_isolated_from_rsvp_society():
    state = read("infrastructure/bootstrap-state/main.tf")
    variables = read("infrastructure/bootstrap-state/variables.tf")
    backend_examples = list((ROOT / "infrastructure").glob("**/backend.hcl.example"))

    assert 'default     = "rsvp-cloud-platform-terraform-locks"' in variables
    assert 'name          = "alias/rsvp-cloud-platform-terraform-state"' in state
    assert 'bucket = "rsvp-cloud-platform-tf-access-${data.aws_caller_identity.current.account_id}-${var.aws_region}"' in state
    for path in backend_examples:
        content = path.read_text()
        assert 'dynamodb_table = "rsvp-terraform-locks"' not in content, path


def test_security_control_scp_blocks_reconfiguration_bypasses():
    scp = read("infrastructure/project-3-cloud-governance/organization/scps.tf")
    for action in [
        "cloudtrail:UpdateTrail",
        "cloudtrail:PutEventSelectors",
        "config:PutConfigurationRecorder",
        "config:PutDeliveryChannel",
        "guardduty:UpdateDetector",
        "securityhub:BatchDisableStandards",
    ]:
        assert f'"{action}"' in scp

def test_dashboard_api_deployment_tracks_full_api_configuration():
    api = read("infrastructure/project-3-cloud-governance/workload/api.tf")
    for token in [
        "options_methods               = aws_api_gateway_method.options",
        "options_integrations          = aws_api_gateway_integration.options",
        "options_method_responses      = aws_api_gateway_method_response.options",
        "options_integration_responses = aws_api_gateway_integration_response.options",
        "authorizer                    = aws_api_gateway_authorizer.cognito",
        "default_4xx                   = aws_api_gateway_gateway_response.default_4xx",
        "default_5xx                   = aws_api_gateway_gateway_response.default_5xx",
    ]:
        assert token in api

def test_security_control_scp_has_no_wildcard_admin_bypass():
    variables = read("infrastructure/project-3-cloud-governance/organization/variables.tf")
    scp = read("infrastructure/project-3-cloud-governance/organization/scps.tf")
    assert 'default     = []' in variables
    assert 'strcontains(arn, "*")' in variables
    assert 'arn:aws:iam::*:role/SecurityAdmin' not in variables
    assert 'for_each = length(var.protected_admin_role_patterns) > 0 ? [1] : []' in scp


def test_workload_environment_and_cognito_deletion_protection_are_guarded():
    variables = read("infrastructure/project-3-cloud-governance/workload/variables.tf")
    api = read("infrastructure/project-3-cloud-governance/workload/api.tf")
    assert 'contains(["dev", "stage", "prod"], var.environment)' in variables
    assert 'deletion_protection = var.environment == "prod" ? "ACTIVE" : "INACTIVE"' in api


def test_runbook_requires_existing_account_ou_placement_verification():
    runbook = read("docs/DEPLOYMENT.md")
    assert "does not move those accounts" in runbook
    assert "An account outside the target OU will not inherit that OU's SCPs." in runbook



def test_lambda_customer_kms_keys_allow_lambda_package_decryption():
    configs = {
        "p1": (
            read("infrastructure/project-1-cloud-platform/observability-security.tf"),
            "${local.name_prefix}-ai-log-summarizer",
        ),
        "security": (
            read("infrastructure/project-3-cloud-governance/security-admin/observability.tf"),
            "${var.project_name}-ai-security-analyzer",
        ),
        "finops": (
            read("infrastructure/project-3-cloud-governance/finops-ai/observability.tf"),
            "${var.project_name}-ai-finops-analyzer",
        ),
        "dashboard": (
            read("infrastructure/project-3-cloud-governance/workload/observability.tf"),
            "${var.project_name}-${var.environment}-dashboard-api",
        ),
    }
    for content, function_name in configs.values():
        assert 'Sid       = "AllowLambdaPackageEncryption"' in content
        assert 'Principal = { Service = "lambda.amazonaws.com" }' in content
        assert '"kms:GenerateDataKey"' in content
        assert '"kms:Decrypt"' in content
        assert (
            '"kms:EncryptionContext:aws:lambda:FunctionArn" = '
            f'"arn:aws:lambda:${{var.aws_region}}:${{data.aws_caller_identity.current.account_id}}:function:{function_name}"'
        ) in content


def test_project3_lambda_customer_kms_keys_allow_lambda_service_for_exact_functions():
    cases = [
        (
            "infrastructure/project-3-cloud-governance/security-admin/observability.tf",
            "arn:aws:lambda:${var.aws_region}:${data.aws_caller_identity.current.account_id}:function:${var.project_name}-ai-security-analyzer",
        ),
        (
            "infrastructure/project-3-cloud-governance/finops-ai/observability.tf",
            "arn:aws:lambda:${var.aws_region}:${data.aws_caller_identity.current.account_id}:function:${var.project_name}-ai-finops-analyzer",
        ),
        (
            "infrastructure/project-3-cloud-governance/workload/observability.tf",
            "arn:aws:lambda:${var.aws_region}:${data.aws_caller_identity.current.account_id}:function:${var.project_name}-${var.environment}-dashboard-api",
        ),
    ]
    for relative_path, function_arn in cases:
        policy = read(relative_path)
        assert 'Sid       = "AllowLambdaPackageEncryption"' in policy
        assert 'Sid       = "AllowLambdaFunctionEncryption"' not in policy
        assert 'Principal = { Service = "lambda.amazonaws.com" }' in policy
        assert '"kms:GenerateDataKey"' in policy
        assert '"kms:Decrypt"' in policy
        assert '"kms:EncryptionContext:aws:lambda:FunctionArn"' in policy
        assert function_arn in policy


def test_project2_container_image_validation_rejects_all_mutable_tags():
    variables = read("infrastructure/project-2-ecs-cicd/terraform/variables.tf")
    assert '@sha256:[0-9a-fA-F]{64}' in variables
    assert ':[0-9a-fA-F]{40}' in variables
    assert 'mutable tags and non-ECR registries are not allowed' in variables
    assert '!endswith(var.container_image, ":latest")' not in variables



def test_ecs_deploy_preserves_supported_task_definition_fields():
    workflow = read(".github/workflows/ecs-project2-deploy.yml")
    assert ".containerDefinitions |= map(" in workflow
    assert "del(" in workflow
    for generated_field in (
        ".taskDefinitionArn",
        ".revision",
        ".status",
        ".requiresAttributes",
        ".compatibilities",
        ".registeredAt",
        ".registeredBy",
    ):
        assert generated_field in workflow
    assert "              family," not in workflow
    assert "              taskRoleArn," not in workflow


def test_governance_dashboard_disables_public_cognito_signup():
    api = read("infrastructure/project-3-cloud-governance/workload/api.tf")
    assert 'admin_create_user_config {' in api
    assert 'allow_admin_create_user_only = true' in api
    assert 'mfa_configuration = "ON"' in api


def test_project2_ecs_container_runs_nonroot_with_readonly_root_filesystem():
    ecs = read("infrastructure/project-2-ecs-cicd/terraform/ecs.tf")
    assert 'user      = "app"' in ecs
    assert 'readonlyRootFilesystem = true' in ecs
    assert 'sourceVolume  = "tmp"' in ecs
    assert 'containerPath = "/tmp"' in ecs
    assert 'readOnly      = false' in ecs
    assert 'volume {' in ecs
    assert 'name = "tmp"' in ecs



def test_stacksets_delegated_admin_requires_cloudformation_trusted_access_opt_in():
    org = (ROOT / "infrastructure/project-3-cloud-governance/organization/organization.tf").read_text()
    delegated = (ROOT / "infrastructure/project-3-cloud-governance/organization/delegated-admin.tf").read_text()
    variables = (ROOT / "infrastructure/project-3-cloud-governance/organization/variables.tf").read_text()
    readme = read("docs/DEPLOYMENT.md")

    assert 'variable "stacksets_trusted_access_activated"' in variables
    assert 'var.stacksets_trusted_access_activated ? ["stacksets.cloudformation.amazonaws.com"] : []' in org
    assert 'var.configure_delegated_admins && var.stacksets_trusted_access_activated' in delegated
    assert "ActivateOrganizationsAccess" in readme


def test_project2_deploy_inherits_latest_terraform_task_definition_baseline():
    ecs = read("infrastructure/project-2-ecs-cicd/terraform/ecs.tf")
    bootstrap = read("infrastructure/project-2-ecs-cicd/bootstrap-delivery/main.tf")
    workflow = read(".github/workflows/ecs-project2-deploy.yml")
    assert 'ConfigurationSource = "TerraformBaseline"' in ecs
    assert '"ecs:ListTaskDefinitions"' in bootstrap
    assert 'name: Resolve Terraform task-definition baseline' in workflow
    assert 'SOURCE=$(aws ecs describe-task-definition' in workflow
    assert '[ "$SOURCE" = "TerraformBaseline" ]' in workflow
    assert '--task-definition "$BASE_TASK_DEF"' in workflow
    assert '--task-definition "$PREVIOUS_TASK_DEF"' in workflow  # rollback target remains actual prior release


def test_organization_member_account_escape_guardrail_covers_root_and_account_closure():
    scp = read("infrastructure/project-3-cloud-governance/organization/scps.tf")
    assert '"organizations:LeaveOrganization"' in scp
    assert '"account:CloseAccount"' in scp
    assert 'resource "aws_organizations_policy_attachment" "deny_leave_root"' in scp
    assert 'target_id = aws_organizations_organization.this.roots[0].id' in scp
    assert 'deny_leave_workloads' not in scp
    assert 'deny_leave_security' not in scp



def test_cloudtrail_bucket_key_has_required_service_decrypt_permission():
    tf = read("infrastructure/project-3-cloud-governance/log-archive/main.tf")
    assert 'bucket_key_enabled = true' in tf
    assert 'sid    = "AllowCloudTrailDecryptForBucketKey"' in tf
    assert 'actions   = ["kms:Decrypt"]' in tf
    assert 'identifiers = ["cloudtrail.amazonaws.com"]' in tf


def test_config_aggregator_does_not_overclaim_member_recording():
    main_readme = (ROOT / "README.md").read_text()
    assert "where Config recording is enabled" in main_readme


def test_project1_recovery_kms_keys_cannot_be_destroyed_with_recovery_data():
    rds = read("infrastructure/project-1-cloud-platform/rds.tf")
    backup = read("infrastructure/project-1-cloud-platform/backup.tf")

    for content in (rds, backup):
        assert "prevent_destroy = true" in content
        assert "deletion_window_in_days = 30" in content
    assert "skip_final_snapshot       = false" in rds
    assert 'resource "aws_backup_vault_lock_configuration" "production"' in backup


def test_provider_constraints_are_minor_series_bounded():
    terraform_files = list((ROOT / "infrastructure").rglob("*.tf"))
    combined = "\n".join(path.read_text() for path in terraform_files)
    assert 'version = "~> 5.65"' not in combined
    assert 'version = "~> 2.4"' not in combined
    assert 'version = "~> 4.0"' not in combined
    assert 'version = "~> 5.65.0"' in combined


def test_workload_vpcs_neutralize_default_security_groups():
    p1 = read("infrastructure/project-1-cloud-platform/vpc.tf")
    p2 = read("infrastructure/project-2-ecs-cicd/terraform/vpc.tf")
    for content in (p1, p2):
        assert 'resource "aws_default_security_group" "default"' in content
    assert 'vpc_id = aws_vpc.main.id' in p1
    assert 'vpc_id = aws_vpc.this.id' in p2


def test_workload_security_groups_avoid_all_protocol_world_egress():
    p1 = read("infrastructure/project-1-cloud-platform/vpc.tf")
    p2 = read("infrastructure/project-2-ecs-cicd/terraform/security_groups.tf")
    assert 'resource "aws_vpc_security_group_egress_rule" "alb_to_app"' in p1
    assert 'resource "aws_vpc_security_group_egress_rule" "app_to_db"' in p1
    assert 'description       = "HTTPS for OS updates and AWS service APIs through NAT"' in p1
    assert 'resource "aws_vpc_security_group_egress_rule" "alb_to_ecs"' in p2
    assert 'description       = "HTTPS to ECR, CloudWatch, and required AWS APIs through NAT"' in p2
    assert 'ip_protocol = "-1"' not in p1
    assert 'ip_protocol = "-1"' not in p2


def test_security_group_references_are_standalone_rules_to_avoid_tf_cycles():
    p1 = read("infrastructure/project-1-cloud-platform/vpc.tf")
    p2 = read("infrastructure/project-2-ecs-cicd/terraform/security_groups.tf")
    for content in (p1, p2):
        assert 'referenced_security_group_id' in content
        assert 'security_groups = [' not in content


def test_project1_asg_tracks_concrete_launch_template_version():
    ec2 = read("infrastructure/project-1-cloud-platform/ec2.tf")
    assert "version = aws_launch_template.app_lt.latest_version" in ec2
    assert 'version = "$Latest"' not in ec2
    assert 'triggers = ["launch_template"]' in ec2


def test_project2_workflows_follow_configurable_region_and_project_name():
    deploy = read(".github/workflows/ecs-project2-deploy.yml")
    bootstrap = read(".github/workflows/ecs-project2-bootstrap-image.yml")
    for workflow in (deploy, bootstrap):
        assert 'AWS_REGION: ${{ vars.AWS_REGION }}' in workflow
        assert 'PROJECT_NAME: ${{ vars.PROJECT_NAME }}' in workflow
        assert 'REGION="${AWS_REGION:-us-east-1}"' in workflow
        assert 'PROJECT="${PROJECT_NAME:-rsvp-project2}"' in workflow
        assert 'ECR_REPOSITORY=$PROJECT-${{ inputs.environment }}-app' in workflow
        assert 'AWS_REGION: us-east-1' not in workflow
    assert 'ECS_CLUSTER=$PROJECT-${{ inputs.environment }}-cluster' in deploy
    assert 'ECS_SERVICE=$PROJECT-${{ inputs.environment }}-service' in deploy
    assert 'ECS_TASK_DEFINITION_FAMILY=$PROJECT-${{ inputs.environment }}-task' in deploy


def test_project1_project_name_respects_alb_name_limit():
    variables = read("infrastructure/project-1-cloud-platform/variables.tf")
    assert '^[a-z0-9]([a-z0-9-]{0,20}[a-z0-9])?$' in variables
    assert 'project_name must be 1-22 characters' in variables
    assert "32-character limit" in variables


def test_project2_container_image_requires_immutable_ecr_uri():
    variables = read("infrastructure/project-2-ecs-cicd/terraform/variables.tf")
    assert 'dkr\\\\.ecr' in variables
    assert 'amazonaws\\\\.com' in variables
    assert '@sha256:[0-9a-fA-F]{64}' in variables
    assert ':[0-9a-fA-F]{40}' in variables
    assert 'non-ECR registries are not allowed' in variables
    assert '(?:' not in variables


def test_project2_immutable_image_workflows_are_idempotent():
    bootstrap_iam = read("infrastructure/project-2-ecs-cicd/bootstrap-delivery/main.tf")
    deploy = read(".github/workflows/ecs-project2-deploy.yml")
    first = read(".github/workflows/ecs-project2-bootstrap-image.yml")
    for action in [
        '"ecr:BatchGetImage"',
        '"ecr:DescribeImages"',
        '"ecr:GetDownloadUrlForLayer"',
    ]:
        assert action in bootstrap_iam
    for workflow in (deploy, first):
        assert 'aws ecr describe-images' in workflow
        assert 'ImageNotFoundException' in workflow
        assert 'docker pull "$IMAGE_URI"' in workflow
        assert 'docker build -t "$IMAGE_URI"' in workflow
        assert "if: env.IMAGE_EXISTS != 'true'" in workflow
        assert 'run: docker push "$IMAGE_URI"' in workflow
        assert 'image-ref: ${{ env.IMAGE_URI }}' in workflow


def test_project2_project_name_contract_is_consistent():
    runtime = read("infrastructure/project-2-ecs-cicd/terraform/variables.tf")
    bootstrap = read("infrastructure/project-2-ecs-cicd/bootstrap-delivery/variables.tf")
    deploy = read(".github/workflows/ecs-project2-deploy.yml")
    first = read(".github/workflows/ecs-project2-bootstrap-image.yml")
    for variables in (runtime, bootstrap):
        assert '^[a-z0-9]([a-z0-9-]{0,20}[a-z0-9])?$' in variables
        assert 'project_name must be 1-22 characters' in variables
    for workflow in (deploy, first):
        assert '${#PROJECT}' in workflow
        assert 'PROJECT_NAME must be 22 characters or fewer' in workflow
        assert "-*|*-)" in workflow


def test_alb_log_buckets_are_versioned_without_unbounded_noncurrent_versions():
    p1 = read("infrastructure/project-1-cloud-platform/observability-security.tf")
    p2 = read("infrastructure/project-2-ecs-cicd/terraform/observability-security.tf")
    for content in (p1, p2):
        assert 'resource "aws_s3_bucket_versioning" "alb_access_logs"' in content
        assert 'status = "Enabled"' in content
        assert 'noncurrent_version_expiration {' in content
        assert 'noncurrent_days = 180' in content


def test_rds_engine_version_description_matches_auto_minor_upgrade_behavior():
    variables = read("infrastructure/project-1-cloud-platform/variables.tf")
    rds = read("infrastructure/project-1-cloud-platform/rds.tf")
    assert 'MySQL engine major version; AWS-managed minor version upgrades remain enabled' in variables
    assert 'auto_minor_version_upgrade = true' in rds
    assert 'Pinned MySQL engine version' not in variables


def test_ai_dynamodb_tables_have_explicit_ttl_retention():
    cases = [
        ("infrastructure/project-1-cloud-platform/ai-logs.tf", 'RETENTION_DAYS    = "90"'),
        ("infrastructure/project-3-cloud-governance/security-admin/ai-operations.tf", 'RETENTION_DAYS           = "180"'),
        ("infrastructure/project-3-cloud-governance/finops-ai/main.tf", 'RETENTION_DAYS    = "365"'),
    ]
    for path, env_token in cases:
        content = read(path)
        assert 'attribute_name = "expires_at"' in content
        assert 'enabled        = true' in content
        assert env_token in content


def test_all_environment_backend_configs_are_templates_not_tracked_runtime_files():
    for base in [
        ROOT / "infrastructure/project-1-cloud-platform/environments",
        ROOT / "infrastructure/project-2-ecs-cicd/terraform/environments",
    ]:
        for env in ("dev", "stage", "prod"):
            directory = base / env
            assert (directory / "backend.hcl.example").exists()
            assert not (directory / "backend.hcl").exists()
    gitignore = (ROOT / ".gitignore").read_text()
    assert "backend.hcl" in gitignore.splitlines()


def test_rds_recovery_script_returns_actual_recovery_points():
    script = read("ops/recovery/validate-rds-recovery.sh")
    assert "sort_by(RecoveryPoints,&CreationDate)[-5:].{Created:CreationDate,Status:Status,ResourceArn:ResourceArn}" in script
    assert ".{Latest:[].{" not in script
    assert "--output json" in script


def test_project2_dependencies_reference_published_pinned_versions():
    requirements = read("infrastructure/project-2-ecs-cicd/app/requirements.txt")
    dockerfile = read("infrastructure/project-2-ecs-cicd/app/Dockerfile")
    assert "flask==3.1.3" in requirements.lower()
    assert "gunicorn==26.2.0" in requirements.lower()
    assert "gunicorn==26.2.2" not in requirements.lower()
    assert "pip install --no-cache-dir --upgrade pip" not in dockerfile
    assert "pip install --no-cache-dir -r requirements.txt" in dockerfile


def test_ci_uses_least_privilege_github_token_permissions():
    ci = read(".github/workflows/ci.yml")
    assert "permissions:\n  contents: read\n" in ci
    assert "security-events: write" not in ci


def test_rds_slow_query_export_is_actually_enabled_without_general_log_noise():
    rds = read("infrastructure/project-1-cloud-platform/rds.tf")
    observability = read("infrastructure/project-1-cloud-platform/observability-security.tf")
    assert 'name  = "slow_query_log"' in rds
    assert 'value = "1"' in rds
    assert 'name  = "log_output"' in rds
    assert 'value = "FILE"' in rds
    assert '"slowquery"' in rds
    assert '"general"' not in rds
    assert 'toset(["error", "slowquery"])' in observability


def test_rds_waits_for_enhanced_monitoring_role_policy():
    rds = read("infrastructure/project-1-cloud-platform/rds.tf")
    assert "aws_iam_role_policy_attachment.rds_monitoring" in rds


def test_first_workloads_wait_for_required_iam_policy_attachments():
    ecs_service = read("infrastructure/project-2-ecs-cicd/terraform/ecs_service.tf")
    ec2 = read("infrastructure/project-1-cloud-platform/ec2.tf")

    assert "aws_iam_role_policy_attachment.ecs_task_execution_policy" in ecs_service
    assert "aws_iam_role_policy_attachment.ec2_basic_ssm" in ec2
    assert "aws_iam_role_policy_attachment.ec2_cloudwatch_logs" in ec2


def test_cloudtrail_bucket_key_decrypt_is_scoped_to_the_organization_trail():
    tf = read("infrastructure/project-3-cloud-governance/log-archive/main.tf")
    block = tf.split('sid    = "AllowCloudTrailDecryptForBucketKey"', 1)[1].split("  }\n}", 1)[0]
    assert 'actions   = ["kms:Decrypt"]' in block
    assert 'variable = "aws:SourceArn"' in block
    assert "values   = [local.trail_arn]" in block


def test_backup_selection_waits_for_backup_role_permissions():
    backup = read("infrastructure/project-1-cloud-platform/backup.tf")
    block = backup.split('resource "aws_backup_selection" "rds"', 1)[1]
    assert "aws_iam_role_policy_attachment.backup" in block
    assert "aws_iam_role_policy_attachment.backup_restore" in block


def test_project2_runtime_configuration_is_not_dead_or_overstated():
    app = read("infrastructure/project-2-ecs-cicd/app/app.py")
    ecs = read("infrastructure/project-2-ecs-cicd/terraform/ecs.tf")
    assert 'SERVICE_NAME = os.getenv("SERVICE_NAME", "RSVP Cloud Service")' in app
    assert 'name  = "SERVICE_NAME"' in ecs
    assert "AI-assisted incident analysis" not in app
    assert "CloudWatch metrics, logs, alarms, and SNS alerting" in app


def test_workflow_python_tooling_is_version_pinned_and_does_not_upgrade_pip():
    ci = read(".github/workflows/ci.yml")
    deploy = read(".github/workflows/ecs-project2-deploy.yml")
    bootstrap = read(".github/workflows/ecs-project2-bootstrap-image.yml")
    for workflow in (ci, deploy, bootstrap):
        assert "python -m pip install --upgrade pip" not in workflow
        assert "pytest==9.1.1" in workflow
    assert "pip-audit==2.10.1" in ci
    assert "ruff==0.16.10" in ci


def test_readme_describes_rds_backup_encryption_accurately():
    readme = (ROOT / "README.md").read_text()
    assert "RDS recovery points inherit the database encryption key" in readme


def test_runtime_services_wait_for_required_iam_permissions():
    p1 = read("infrastructure/project-1-cloud-platform/ai-logs.tf")
    workload = read("infrastructure/project-3-cloud-governance/workload/api.tf")
    workload_iam = read("infrastructure/project-3-cloud-governance/workload/api_iam.tf")
    finops = read("infrastructure/project-3-cloud-governance/finops-ai/main.tf")
    security = read("infrastructure/project-3-cloud-governance/security-admin/ai-operations.tf")

    for token in (
        "aws_iam_role_policy_attachment.lambda_basic_execution",
        "aws_iam_role_policy_attachment.lambda_xray",
        "aws_iam_role_policy_attachment.ai_lambda_policy_attach",
    ):
        assert token in p1
    for token in (
        "aws_iam_role_policy_attachment.dashboard_api_logs",
        "aws_iam_role_policy_attachment.dashboard_xray",
        "aws_iam_role_policy.dashboard_api_inline",
    ):
        assert token in workload
    assert "depends_on = [aws_iam_role_policy_attachment.apigw_logs]" in workload_iam
    for token in (
        "aws_iam_role_policy_attachment.logs",
        "aws_iam_role_policy_attachment.xray",
        "aws_iam_role_policy.lambda",
    ):
        assert token in finops
    for token in (
        "aws_iam_role_policy_attachment.ai_incident_logs",
        "aws_iam_role_policy_attachment.ai_incident_xray",
        "aws_iam_role_policy.ai_incident",
    ):
        assert token in security


def test_github_deploy_scopes_task_definition_registration_to_environment_family():
    bootstrap = read("infrastructure/project-2-ecs-cicd/bootstrap-delivery/main.tf")
    assert 'sid = "EcsTaskDefinitionRead"' in bootstrap
    assert '"ecs:DescribeTaskDefinition"' in bootstrap
    assert '"ecs:ListTaskDefinitions"' in bootstrap
    assert 'sid     = "EcsTaskDefinitionRegister"' in bootstrap
    assert 'actions = ["ecs:RegisterTaskDefinition"]' in bootstrap
    assert 'task-definition/${var.project_name}-${each.key}-task:*' in bootstrap
    register_block = bootstrap.split('sid     = "EcsTaskDefinitionRegister"', 1)[1].split("  }", 1)[0]
    assert 'resources = ["*"]' not in register_block


def test_predeploy_runbook_explains_ecs_task_definition_ownership_handoff():
    runbook = read("docs/DEPLOYMENT.md")
    assert "Task-definition ownership" in runbook
    assert "ConfigurationSource=TerraformBaseline" in runbook
    assert "after any Terraform change that modifies the ECS task definition" in runbook
    assert "run **Controlled Deploy**" in runbook


def test_project1_rds_engine_contract_matches_mysql_specific_controls():
    variables = read("infrastructure/project-1-cloud-platform/variables.tf")
    rds = read("infrastructure/project-1-cloud-platform/rds.tf")
    assert 'condition     = var.rds_engine == "mysql"' in variables
    assert 'error_message = "rds_engine must be mysql for this stack."' in variables
    assert 'name  = "slow_query_log"' in rds
    assert 'name  = "log_output"' in rds


def test_checkov_alb_exceptions_are_scoped_to_real_aws_or_environment_constraints():
    root = Path(__file__).resolve().parents[1]
    global_cfg = (root / ".checkov.yml").read_text()
    assert "CKV_AWS_145" not in global_cfg
    assert "CKV_AWS_150" not in global_cfg

    p1_alb = (root / "infrastructure/project-1-cloud-platform/alb.tf").read_text()
    p2_alb = (root / "infrastructure/project-2-ecs-cicd/terraform/alb.tf").read_text()
    p1_obs = (root / "infrastructure/project-1-cloud-platform/observability-security.tf").read_text()
    p2_obs = (root / "infrastructure/project-2-ecs-cicd/terraform/observability-security.tf").read_text()

    for alb in (p1_alb, p2_alb):
        assert "#checkov:skip=CKV_AWS_150:" in alb
        assert 'enable_deletion_protection = var.environment == "prod"' in alb

    for obs in (p1_obs, p2_obs):
        assert "#checkov:skip=CKV_AWS_145:" in obs
        assert 'sse_algorithm = "AES256"' in obs
        assert "Legacy ALB access-log destinations support SSE-S3" in obs


def test_sensitive_s3_sources_have_access_logging_and_log_sinks_do_not_recurse():
    root = Path(__file__).resolve().parents[1]
    bootstrap = (root / "infrastructure/bootstrap-state/main.tf").read_text()
    p1_ai = (root / "infrastructure/project-1-cloud-platform/ai-logs.tf").read_text()
    p1_obs = (root / "infrastructure/project-1-cloud-platform/observability-security.tf").read_text()
    p2_obs = (root / "infrastructure/project-2-ecs-cicd/terraform/observability-security.tf").read_text()
    archive = (root / "infrastructure/project-3-cloud-governance/log-archive/main.tf").read_text()
    global_cfg = (root / ".checkov.yml").read_text()

    assert 'resource "aws_s3_bucket_logging" "terraform_state"' in bootstrap
    assert 'target_bucket = aws_s3_bucket.state_access_logs.id' in bootstrap
    assert 'identifiers = ["logging.s3.amazonaws.com"]' in bootstrap
    assert 'aws:SourceArn' in bootstrap
    assert 'aws:SourceAccount' in bootstrap
    assert '#checkov:skip=CKV_AWS_18:' in bootstrap
    assert '#checkov:skip=CKV_AWS_145:' in bootstrap

    assert 'resource "aws_s3_bucket_logging" "ai_logs"' in p1_ai
    assert 'target_bucket = aws_s3_bucket.alb_access_logs.id' in p1_ai
    assert 's3-access/ai-logs/' in p1_ai
    assert 'identifiers = ["logging.s3.amazonaws.com"]' in p1_obs

    for sink in (p1_obs, p2_obs, archive):
        assert '#checkov:skip=CKV_AWS_18:' in sink

    assert "CKV_AWS_18" not in global_cfg
    assert "CKV_AWS_145" not in global_cfg


def test_cross_variable_capacity_and_storage_contracts_fail_early():
    root = Path(__file__).resolve().parents[1]
    p1 = (root / "infrastructure/project-1-cloud-platform/prerequisites.tf").read_text()
    p2 = (root / "infrastructure/project-2-ecs-cicd/terraform/prerequisites.tf").read_text()
    p2_vars = (root / "infrastructure/project-2-ecs-cicd/terraform/variables.tf").read_text()

    assert "var.rds_max_allocated_storage >= ceil(var.rds_allocated_storage * 1.10)" in p1
    assert "var.rds_allocated_storage >= 20" in p1
    assert "length(distinct(concat(" in p1
    assert "var.ecs_min_capacity >= 1" in p2
    assert "var.ecs_max_capacity >= var.ecs_min_capacity" in p2
    assert "var.ecs_cpu_target >= 10 && var.ecs_cpu_target <= 90" in p2_vars
    assert "var.ecs_memory_target >= 10 && var.ecs_memory_target <= 90" in p2_vars
    assert "CloudWatch Logs supported retention value" in p2_vars


def test_project1_first_boot_is_bounded_and_rds_teardown_semantics_are_environment_aware():
    root = Path(__file__).resolve().parents[1]
    ec2 = (root / "infrastructure/project-1-cloud-platform/ec2.tf").read_text()
    rds = (root / "infrastructure/project-1-cloud-platform/rds.tf").read_text()
    global_cfg = (root / ".checkov.yml").read_text()

    assert "yum update -y" not in ec2
    assert "dnf install -y httpd amazon-cloudwatch-agent" in ec2
    assert 'deletion_protection       = var.environment == "prod"' in rds
    assert "#checkov:skip=CKV_AWS_293:" in rds
    assert 'formatdate("YYYYMMDDhhmmss", timestamp())' in rds
    assert "ignore_changes = [final_snapshot_identifier]" in rds
    assert "CKV_AWS_293" not in global_cfg


def test_all_customer_managed_kms_keys_have_explicit_key_policy_ownership():
    root = Path(__file__).resolve().parents[1]
    targets = [
        root / "infrastructure/bootstrap-state/main.tf",
        root / "infrastructure/project-1-cloud-platform/backup.tf",
        root / "infrastructure/project-1-cloud-platform/ai-logs.tf",
        root / "infrastructure/project-1-cloud-platform/rds.tf",
        root / "infrastructure/project-2-ecs-cicd/bootstrap-delivery/main.tf",
    ]
    for path in targets:
        content = path.read_text()
        assert 'Sid       = "EnableAccountAdministration"' in content
        assert 'Principal = { AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root" }' in content
        assert 'Action    = "kms:*"' in content

    archive = (root / "infrastructure/project-3-cloud-governance/log-archive/main.tf").read_text()
    assert 'resource "aws_kms_key_policy" "audit"' in archive
    assert 'data "aws_iam_policy_document" "kms"' in archive
