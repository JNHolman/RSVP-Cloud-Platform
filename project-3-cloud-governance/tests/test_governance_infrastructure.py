from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(relative_path):
    return (ROOT / relative_path).read_text()


def test_governance_lambda_logs_are_explicit_and_encrypted():
    security = read("project-3-cloud-governance/security-admin/observability.tf")
    finops = read("project-3-cloud-governance/finops-ai/observability.tf")
    workload = read("project-3-cloud-governance/workload/observability.tf")

    for content in (security, finops, workload):
        assert 'resource "aws_kms_key" "observability"' in content
        assert "kms_key_id        = aws_kms_key.observability.arn" in content


def test_identity_center_fails_with_explicit_prerequisite():
    identity = read("project-3-cloud-governance/identity-center/main.tf")
    assert "identity_center_instances" in identity
    assert "length(local.identity_center_instances) == 1" in identity
    assert "IAM Identity Center must be enabled" in identity
    assert "tolist(data.aws_ssoadmin_instances.this.arns)[0]" not in identity


def test_organization_enables_cloudtrail_trusted_access():
    organization = read("project-3-cloud-governance/organization/organization.tf")
    assert '"cloudtrail.amazonaws.com"' in organization


def test_organization_preserves_identity_center_trusted_access():
    organization = read("project-3-cloud-governance/organization/organization.tf")
    assert '"sso.amazonaws.com"' in organization


def test_governance_dynamodb_uses_customer_managed_kms():
    security = read("project-3-cloud-governance/security-admin/ai-operations.tf")
    finops = read("project-3-cloud-governance/finops-ai/main.tf")

    # The tables remain encrypted by the customer-managed observability keys.
    for content in (security, finops):
        assert "kms_key_arn = aws_kms_key.observability.arn" in content

    # DynamoDB performs table encryption transparently and creates/uses its own
    # KMS grants. Runtime application roles must not administer those grants.
    for content in (security, finops):
        assert '"kms:CreateGrant"' not in content
        assert 'StringLike = { "kms:ViaService" = "dynamodb.*.amazonaws.com" }' not in content


def test_dashboard_data_model_returns_recent_records_deterministically():
    security = read("project-3-cloud-governance/security-admin/ai-operations.tf")
    finops = read("project-3-cloud-governance/finops-ai/main.tf")
    dashboard = read("project-3-cloud-governance/workload/dashboard_api.py")
    sec_handler = read("project-3-cloud-governance/security-admin/ai_incident_analyzer.py")
    fin_handler = read("project-3-cloud-governance/finops-ai/cost_analyzer.py")

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
    variables = read("project-3-cloud-governance/workload/variables.tf")
    assert variables.count("must be a valid IAM role ARN") == 2
    assert "ai_incidents_table_name must not be empty" in variables
    assert "ai_cost_summaries_table_name must not be empty" in variables


def test_log_archive_has_destruction_safeguards():
    archive = read("project-3-cloud-governance/log-archive/main.tf")
    assert archive.count("prevent_destroy = true") >= 2


def test_security_control_scp_blocks_reconfiguration_bypasses():
    scp = read("project-3-cloud-governance/modules/scp-policies/main.tf")
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
    api = read("project-3-cloud-governance/workload/api.tf")
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


def test_workload_environment_and_cognito_deletion_protection_are_guarded():
    variables = read("project-3-cloud-governance/workload/variables.tf")
    api = read("project-3-cloud-governance/workload/api.tf")
    assert 'contains(["dev", "stage", "prod"], var.environment)' in variables
    assert 'deletion_protection = var.environment == "prod" ? "ACTIVE" : "INACTIVE"' in api


def test_project3_lambda_customer_kms_keys_allow_lambda_service_for_exact_functions():
    cases = [
        (
            "project-3-cloud-governance/security-admin/observability.tf",
            "arn:aws:lambda:${var.aws_region}:${data.aws_caller_identity.current.account_id}:function:${var.project_name}-ai-security-analyzer",
        ),
        (
            "project-3-cloud-governance/finops-ai/observability.tf",
            "arn:aws:lambda:${var.aws_region}:${data.aws_caller_identity.current.account_id}:function:${var.project_name}-ai-finops-analyzer",
        ),
        (
            "project-3-cloud-governance/workload/observability.tf",
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


def test_governance_dashboard_disables_public_cognito_signup():
    api = read("project-3-cloud-governance/workload/api.tf")
    assert 'admin_create_user_config {' in api
    assert 'allow_admin_create_user_only = true' in api
    assert 'mfa_configuration = "ON"' in api


def test_organization_member_account_escape_guardrail_covers_root_and_account_closure():
    scp = read("project-3-cloud-governance/organization/scps.tf")
    policy = read("project-3-cloud-governance/modules/scp-policies/main.tf")
    assert '"organizations:LeaveOrganization"' in policy
    assert '"account:CloseAccount"' in policy
    assert 'resource "aws_organizations_policy_attachment" "deny_leave_root"' in scp
    assert 'target_id = aws_organizations_organization.this.roots[0].id' in scp
    assert 'deny_leave_workloads' not in scp
    assert 'deny_leave_security' not in scp


def test_cloudtrail_bucket_key_has_required_service_decrypt_permission():
    tf = read("project-3-cloud-governance/log-archive/main.tf")
    assert 'bucket_key_enabled = true' in tf
    assert 'sid    = "AllowCloudTrailDecryptForBucketKey"' in tf
    assert 'actions   = ["kms:Decrypt"]' in tf
    assert 'identifiers = ["cloudtrail.amazonaws.com"]' in tf


def test_cloudtrail_bucket_key_decrypt_is_scoped_to_the_organization_trail():
    tf = read("project-3-cloud-governance/log-archive/main.tf")
    block = tf.split('sid    = "AllowCloudTrailDecryptForBucketKey"', 1)[1].split("  }\n}", 1)[0]
    assert 'actions   = ["kms:Decrypt"]' in block
    assert 'variable = "aws:SourceArn"' in block
    assert "values   = [local.trail_arn]" in block
