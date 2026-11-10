import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text()


def test_workloads_do_not_receive_public_ips():
    infrastructure = "\n".join(
        path.read_text() for path in ROOT.rglob("*.tf")
    )
    assert "assign_public_ip = true" not in infrastructure
    assert "associate_public_ip_address = true" not in infrastructure


def test_github_oidc_and_deploy_rollback_contract():
    oidc = read("project-2-ecs-cicd/bootstrap-delivery/main.tf")
    workflow = read(".github/workflows/ecs-project2-deploy.yml")

    assert "thumbprint_list" in oidc
    assert "steps.deploy.outcome == 'failure' || steps.smoke.outcome == 'failure'" in workflow
    assert '--task-definition "$PREVIOUS_TASK_DEF"' in workflow
    assert '--task-definition "$ECS_TASK_DEFINITION_FAMILY"' not in workflow
    assert 'case "$SERVICE_URL" in' in workflow
    assert "curl --proto '=https' --tlsv1.2" in workflow


def test_organization_existing_accounts_are_reference_only():
    variables = read("project-3-cloud-governance/organization/variables.tf")
    prerequisites = read("project-3-cloud-governance/organization/prerequisites.tf")

    assert "does not move existing accounts between OUs" in variables
    assert "does not adopt or move those accounts into Terraform-managed OUs" in variables
    assert 'default     = false' in variables
    assert 'resource "terraform_data" "delegated_admin_prerequisites"' in prerequisites


def test_state_bucket_is_protected_and_owner_enforced():
    state = read("shared/bootstrap-state/main.tf")
    assert "prevent_destroy = true" in state
    assert 'object_ownership = "BucketOwnerEnforced"' in state
    assert "block_public_policy     = true" in state
    assert 'sse_algorithm     = "aws:kms"' in state


def test_alarm_topics_use_service_compatible_customer_managed_kms():
    p1_topic = read("project-1-cloud-foundation/terraform/monitoring.tf")
    p2_topic = read("project-2-ecs-cicd/terraform/observability.tf")
    p1_key = read("project-1-cloud-foundation/terraform/observability-security.tf")
    p2_key = read("project-2-ecs-cicd/terraform/observability-security.tf")
    p1_iam = re.sub(r"[ \t]+", " ", read("project-1-cloud-foundation/terraform/iam.tf"))

    assert 'alias/aws/sns' not in p1_topic + p2_topic
    assert 'kms_master_key_id = aws_kms_key.observability.arn' in p1_topic
    assert 'kms_master_key_id = aws_kms_key.observability.arn' in p2_topic
    for key in (p1_key, p2_key):
        assert 'Principal = { Service = "sns.amazonaws.com" }' in key
        assert 'Principal = { Service = "cloudwatch.amazonaws.com" }' in key
    assert 'Sid = "UseAlertTopicKmsKey"' in p1_iam


def test_all_lambda_functions_use_customer_kms_and_xray():
    files = {
        "p1": read("project-1-cloud-foundation/terraform/ai-logs.tf"),
        "security": read("project-3-cloud-governance/security-admin/ai-operations.tf"),
        "finops": read("project-3-cloud-governance/finops-ai/main.tf"),
        "dashboard": read("project-3-cloud-governance/workload/api.tf"),
    }
    for content in files.values():
        assert 'kms_key_arn                    = aws_kms_key.observability.arn' in content
        assert 'tracing_config {' in content
        assert 'mode = "Active"' in content

    attachments = "\n".join([
        read("project-1-cloud-foundation/terraform/iam.tf"),
        files["security"],
        files["finops"],
        read("project-3-cloud-governance/workload/api_iam.tf"),
    ])
    assert attachments.count("AWSXRayDaemonWriteAccess") >= 4


def test_release_validator_cleans_generated_python_artifacts():
    validator = read("shared/validate-release.sh")
    assert "cleanup_generated()" in validator
    assert "trap cleanup_generated EXIT" in validator
    assert "__pycache__" in validator
    assert ".pytest_cache" in validator


def test_public_subnets_do_not_auto_assign_public_ips():
    p1 = read("project-1-cloud-foundation/terraform/vpc.tf")
    p2 = read("project-2-ecs-cicd/terraform/vpc.tf")
    assert "map_public_ip_on_launch = true" not in p1 + p2


def test_albs_enable_desync_mitigation():
    p1 = read("project-1-cloud-foundation/terraform/alb.tf")
    p2 = read("project-2-ecs-cicd/terraform/alb.tf")
    for content in (p1, p2):
        assert 'desync_mitigation_mode     = "defensive"' in content


def test_s3_lifecycle_and_acl_hardening_contracts():
    ai = read("project-1-cloud-foundation/terraform/ai-logs.tf")
    p1_logs = read("project-1-cloud-foundation/terraform/observability-security.tf")
    p2_logs = read("project-2-ecs-cicd/terraform/observability-security.tf")
    audit = read("project-3-cloud-governance/log-archive/main.tf")
    state = read("shared/bootstrap-state/main.tf")
    assert 'object_ownership = "BucketOwnerEnforced"' in ai
    for content in (ai, p1_logs, p2_logs, audit, state):
        assert 'days_after_initiation = 7' in content
    assert 'resource "aws_s3_bucket_lifecycle_configuration" "terraform_state"' in state
    assert 'noncurrent_days = 365' in state


def test_remote_state_locking_is_protected_and_customer_encrypted():
    state = read("shared/bootstrap-state/main.tf")
    assert "deletion_protection_enabled = true" in state
    assert "kms_key_arn = aws_kms_key.terraform_state.arn" in state
    assert state.count("prevent_destroy = true") >= 3


def _terraform_roots():
    roots = set()
    for path in ROOT.rglob("*.tf"):
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
    base = ROOT / "project-3-cloud-governance"
    stacks = ["organization", "audit-trail", "finops-ai", "identity-center", "security-admin", "log-archive", "workload"]
    for stack in stacks:
        example = (base / stack / "backend.hcl.example").read_text()
        assert "REPLACE_WITH_ACCOUNT_LOCAL_TERRAFORM_STATE_BUCKET" in example
        assert 'dynamodb_table = \"rsvp-cloud-platform-terraform-locks\"' in example


def test_cloud_platform_state_names_are_isolated_from_rsvp_society():
    state = read("shared/bootstrap-state/main.tf")
    variables = read("shared/bootstrap-state/variables.tf")
    backend_examples = list(ROOT.glob("**/backend.hcl.example"))

    assert 'default     = "rsvp-cloud-platform-terraform-locks"' in variables
    assert 'name          = "alias/rsvp-cloud-platform-terraform-state"' in state
    assert 'bucket = "rsvp-cloud-platform-tf-access-${data.aws_caller_identity.current.account_id}-${var.aws_region}"' in state
    for path in backend_examples:
        content = path.read_text()
        assert 'dynamodb_table = "rsvp-terraform-locks"' not in content, path


def test_project3_documents_ou_placement_requirement():
    readme = read("project-3-cloud-governance/README.md")
    assert "A policy only protects accounts placed in the right organizational unit." in readme
    assert "Existing accounts need deliberate placement" in readme


def test_lambda_customer_kms_keys_allow_lambda_package_decryption():
    configs = {
        "p1": (
            read("project-1-cloud-foundation/terraform/observability-security.tf"),
            "${local.name_prefix}-ai-log-summarizer",
        ),
        "security": (
            read("project-3-cloud-governance/security-admin/observability.tf"),
            "${var.project_name}-ai-security-analyzer",
        ),
        "finops": (
            read("project-3-cloud-governance/finops-ai/observability.tf"),
            "${var.project_name}-ai-finops-analyzer",
        ),
        "dashboard": (
            read("project-3-cloud-governance/workload/observability.tf"),
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


def test_stacksets_delegated_admin_requires_cloudformation_trusted_access_opt_in():
    org = (ROOT / "project-3-cloud-governance/organization/organization.tf").read_text()
    delegated = (ROOT / "project-3-cloud-governance/organization/delegated-admin.tf").read_text()
    variables = (ROOT / "project-3-cloud-governance/organization/variables.tf").read_text()

    assert 'variable "stacksets_trusted_access_activated"' in variables
    assert 'var.stacksets_trusted_access_activated ? ["stacksets.cloudformation.amazonaws.com"] : []' in org
    assert 'var.configure_delegated_admins && var.stacksets_trusted_access_activated' in delegated
    assert "ActivateOrganizationsAccess" in variables


def test_project2_deploy_inherits_latest_terraform_task_definition_baseline():
    ecs = read("project-2-ecs-cicd/terraform/ecs.tf")
    bootstrap = read("project-2-ecs-cicd/bootstrap-delivery/main.tf")
    workflow = read(".github/workflows/ecs-project2-deploy.yml")
    assert 'ConfigurationSource = "TerraformBaseline"' in ecs
    assert '"ecs:ListTaskDefinitions"' in bootstrap
    assert 'name: Resolve Terraform task-definition baseline' in workflow
    assert 'SOURCE=$(aws ecs describe-task-definition' in workflow
    assert '[ "$SOURCE" = "TerraformBaseline" ]' in workflow
    assert '--task-definition "$BASE_TASK_DEF"' in workflow
    assert '--task-definition "$PREVIOUS_TASK_DEF"' in workflow  # rollback target remains actual prior release


def test_config_aggregator_does_not_overclaim_member_recording():
    readme = read("project-3-cloud-governance/README.md")
    assert "AWS Config can only collect security configuration data from accounts that have recording enabled." in readme


def test_provider_constraints_are_minor_series_bounded():
    terraform_files = list(ROOT.rglob("*.tf"))
    combined = "\n".join(path.read_text() for path in terraform_files)
    assert 'version = "~> 5.65"' not in combined
    assert 'version = "~> 2.4"' not in combined
    assert 'version = "~> 4.0"' not in combined
    assert 'version = "~> 5.65.0"' in combined


def test_workload_vpcs_neutralize_default_security_groups():
    p1 = read("project-1-cloud-foundation/terraform/vpc.tf")
    p2 = read("project-2-ecs-cicd/terraform/vpc.tf")
    for content in (p1, p2):
        assert 'resource "aws_default_security_group" "default"' in content
    assert 'vpc_id = aws_vpc.main.id' in p1
    assert 'vpc_id = aws_vpc.this.id' in p2


def test_workload_security_groups_avoid_all_protocol_world_egress():
    p1 = read("project-1-cloud-foundation/terraform/vpc.tf")
    p2 = read("project-2-ecs-cicd/terraform/security_groups.tf")
    assert 'resource "aws_vpc_security_group_egress_rule" "alb_to_app"' in p1
    assert 'resource "aws_vpc_security_group_egress_rule" "app_to_db"' in p1
    assert 'description       = "HTTPS for OS updates and AWS service APIs through NAT"' in p1
    assert 'resource "aws_vpc_security_group_egress_rule" "alb_to_ecs"' in p2
    assert 'description       = "HTTPS to ECR, CloudWatch, and required AWS APIs through NAT"' in p2
    assert 'ip_protocol = "-1"' not in p1
    assert 'ip_protocol = "-1"' not in p2


def test_security_group_references_are_standalone_rules_to_avoid_tf_cycles():
    p1 = read("project-1-cloud-foundation/terraform/vpc.tf")
    p2 = read("project-2-ecs-cicd/terraform/security_groups.tf")
    for content in (p1, p2):
        assert 'referenced_security_group_id' in content
        assert 'security_groups = [' not in content


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


def test_project2_immutable_image_workflows_are_idempotent():
    bootstrap_iam = read("project-2-ecs-cicd/bootstrap-delivery/main.tf")
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
    runtime = read("project-2-ecs-cicd/terraform/variables.tf")
    bootstrap = read("project-2-ecs-cicd/bootstrap-delivery/variables.tf")
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
    p1 = read("project-1-cloud-foundation/terraform/observability-security.tf")
    p2 = read("project-2-ecs-cicd/terraform/observability-security.tf")
    for content in (p1, p2):
        assert 'resource "aws_s3_bucket_versioning" "alb_access_logs"' in content
        assert 'status = "Enabled"' in content
        assert 'noncurrent_version_expiration {' in content
        assert 'noncurrent_days = 180' in content


def test_ai_dynamodb_tables_have_explicit_ttl_retention():
    cases = [
        ("project-1-cloud-foundation/terraform/ai-logs.tf", 'RETENTION_DAYS    = "90"'),
        ("project-3-cloud-governance/security-admin/ai-operations.tf", 'RETENTION_DAYS           = "180"'),
        ("project-3-cloud-governance/finops-ai/main.tf", 'RETENTION_DAYS    = "365"'),
    ]
    for path, env_token in cases:
        content = read(path)
        assert 'attribute_name = "expires_at"' in content
        assert 'enabled        = true' in content
        assert env_token in content


def test_all_environment_backend_configs_are_templates_not_tracked_runtime_files():
    for base in [
        ROOT / "project-1-cloud-foundation/terraform/environments",
        ROOT / "project-2-ecs-cicd/terraform/environments",
    ]:
        for env in ("dev", "stage", "prod"):
            directory = base / env
            assert (directory / "backend.hcl.example").exists()
            assert not (directory / "backend.hcl").exists()
    gitignore = (ROOT / ".gitignore").read_text()
    assert "backend.hcl" in gitignore.splitlines()


def test_ci_uses_least_privilege_github_token_permissions():
    ci = read(".github/workflows/ci.yml")
    assert "permissions:\n  contents: read\n" in ci
    assert "security-events: write" not in ci


def test_first_workloads_wait_for_required_iam_policy_attachments():
    ecs_service = read("project-2-ecs-cicd/terraform/ecs_service.tf")
    ec2 = read("project-1-cloud-foundation/terraform/ec2.tf")

    assert "aws_iam_role_policy_attachment.ecs_task_execution_policy" in ecs_service
    assert "aws_iam_role_policy_attachment.ec2_basic_ssm" in ec2
    assert "aws_iam_role_policy_attachment.ec2_cloudwatch_logs" in ec2


def test_workflow_python_tooling_is_version_pinned_and_does_not_upgrade_pip():
    ci = read(".github/workflows/ci.yml")
    deploy = read(".github/workflows/ecs-project2-deploy.yml")
    bootstrap = read(".github/workflows/ecs-project2-bootstrap-image.yml")
    for workflow in (ci, deploy, bootstrap):
        assert "python -m pip install --upgrade pip" not in workflow
        assert "pytest==9.1.1" in workflow
    assert "pip-audit==2.10.1" in ci
    assert "ruff==0.16.10" in ci


def test_rds_recovery_keys_and_backup_encryption_are_preserved():
    readme = read("project-1-cloud-foundation/README.md")
    rds = read("project-1-cloud-foundation/terraform/rds.tf")

    assert "storage_encrypted     = true" in rds
    assert "kms_key_id            = aws_kms_key.rds.arn" in rds
    assert "snapshot that survives teardown but loses its decryption key" in readme


def test_runtime_services_wait_for_required_iam_permissions():
    p1 = read("project-1-cloud-foundation/terraform/ai-logs.tf")
    workload = read("project-3-cloud-governance/workload/api.tf")
    workload_iam = read("project-3-cloud-governance/workload/api_iam.tf")
    finops = read("project-3-cloud-governance/finops-ai/main.tf")
    security = read("project-3-cloud-governance/security-admin/ai-operations.tf")

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


def test_ecs_task_definition_ownership_handoff_is_explicit():
    readme = read("project-2-ecs-cicd/README.md")
    service = read("project-2-ecs-cicd/terraform/ecs_service.tf")
    workflow = read(".github/workflows/ecs-project2-deploy.yml")

    assert "Terraform owns the infrastructure baseline" in readme
    assert "GitHub Actions owns **which application revision is released**" in readme
    assert "the controlled release has to promote it intentionally" in readme
    assert "ignore_changes = [" in service and "task_definition," in service
    assert "Capture current task definition for rollback" in workflow


def test_checkov_alb_exceptions_are_scoped_to_real_aws_or_environment_constraints():
    root = Path(__file__).resolve().parents[2]
    global_cfg = (root / ".checkov.yml").read_text()
    assert "CKV_AWS_145" not in global_cfg
    assert "CKV_AWS_150" not in global_cfg

    p1_alb = (root / "project-1-cloud-foundation/terraform/alb.tf").read_text()
    p2_alb = (root / "project-2-ecs-cicd/terraform/alb.tf").read_text()
    p1_obs = (root / "project-1-cloud-foundation/terraform/observability-security.tf").read_text()
    p2_obs = (root / "project-2-ecs-cicd/terraform/observability-security.tf").read_text()

    for alb in (p1_alb, p2_alb):
        assert "#checkov:skip=CKV_AWS_150:" in alb
        assert 'enable_deletion_protection = var.environment == "prod"' in alb

    for obs in (p1_obs, p2_obs):
        assert "#checkov:skip=CKV_AWS_145:" in obs
        assert 'sse_algorithm = "AES256"' in obs
        assert "Legacy ALB access-log destinations support SSE-S3" in obs


def test_sensitive_s3_sources_have_access_logging_and_log_sinks_do_not_recurse():
    root = Path(__file__).resolve().parents[2]
    bootstrap = (root / "shared/bootstrap-state/main.tf").read_text()
    p1_ai = (root / "project-1-cloud-foundation/terraform/ai-logs.tf").read_text()
    p1_obs = (root / "project-1-cloud-foundation/terraform/observability-security.tf").read_text()
    p2_obs = (root / "project-2-ecs-cicd/terraform/observability-security.tf").read_text()
    archive = (root / "project-3-cloud-governance/log-archive/main.tf").read_text()
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
    root = Path(__file__).resolve().parents[2]
    p1 = (root / "project-1-cloud-foundation/terraform/prerequisites.tf").read_text()
    p2 = (root / "project-2-ecs-cicd/terraform/prerequisites.tf").read_text()
    p2_vars = (root / "project-2-ecs-cicd/terraform/variables.tf").read_text()

    assert "var.rds_max_allocated_storage >= ceil(var.rds_allocated_storage * 1.10)" in p1
    assert "var.rds_allocated_storage >= 20" in p1
    assert "length(distinct(concat(" in p1
    assert "var.ecs_min_capacity >= 1" in p2
    assert "var.ecs_max_capacity >= var.ecs_min_capacity" in p2
    assert "var.ecs_cpu_target >= 10 && var.ecs_cpu_target <= 90" in p2_vars
    assert "var.ecs_memory_target >= 10 && var.ecs_memory_target <= 90" in p2_vars
    assert "CloudWatch Logs supported retention value" in p2_vars


def test_all_customer_managed_kms_keys_have_explicit_key_policy_ownership():
    root = Path(__file__).resolve().parents[2]
    targets = [
        root / "shared/bootstrap-state/main.tf",
        root / "project-1-cloud-foundation/terraform/backup.tf",
        root / "project-1-cloud-foundation/terraform/ai-logs.tf",
        root / "project-1-cloud-foundation/terraform/rds.tf",
        root / "project-2-ecs-cicd/bootstrap-delivery/main.tf",
    ]
    for path in targets:
        content = path.read_text()
        assert 'Sid       = "EnableAccountAdministration"' in content
        assert 'Principal = { AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root" }' in content
        assert 'Action    = "kms:*"' in content

    archive = (root / "project-3-cloud-governance/log-archive/main.tf").read_text()
    assert 'resource "aws_kms_key_policy" "audit"' in archive
    assert 'data "aws_iam_policy_document" "kms"' in archive

def test_project3_dashboard_reader_trust_and_security_enrollment():
    root = ROOT / "project-3-cloud-governance"
    for path in ["security-admin/ai-operations.tf", "finops-ai/main.tf"]:
        trust = (root / path).read_text().split('data "aws_iam_policy_document" "dashboard_read_assume" {')[1].split("\n}")[0]
        assert 'identifiers = ["arn:aws:iam::${var.dashboard_reader_account_id}:root"]' in trust
        assert 'test     = "ArnEquals"' in trust
        assert 'variable = "aws:PrincipalArn"' in trust
        assert 'values   = ["arn:aws:iam::${var.dashboard_reader_account_id}:role/${var.dashboard_reader_role_name}"]' in trust
    assert 'auto_enable_organization_members = "ALL"' in (root / "security-admin/guardduty.tf").read_text()
    assert "enable_default_standards = true" in (root / "security-admin/securityhub.tf").read_text()
