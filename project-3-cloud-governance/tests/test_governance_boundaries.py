"""Offline contracts on the enterprise resources that consume the policies."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "project-3-cloud-governance"


def resource(path, kind, name):
    text = (ROOT / path).read_text()
    body = text.split(f'resource "{kind}" "{name}" {{', 1)[1].split("\n}", 1)[0]
    return " ".join(body.split())


def test_member_accounts_are_guarded_and_attached_to_intended_ous():
    for account, ou in {
        "security": "security", "log_archive": "security",
        "shared_services": "infrastructure", "nonprod": "nonprod", "prod": "prod",
    }.items():
        body = resource("organization/accounts.tf", "aws_organizations_account", account)
        assert f"parent_id = aws_organizations_organizational_unit.{ou}.id" in body
        assert "prevent_destroy = true" in body
        assert "count = var.create_member_accounts ? 1 : 0" in body
    for ou in ["prod", "nonprod"]:
        unit = resource("organization/organization.tf", "aws_organizations_organizational_unit", ou)
        assert "parent_id = aws_organizations_organizational_unit.workloads.id" in unit
        guard = resource("organization/scps.tf", "aws_organizations_policy_attachment", f"protect_{ou}")
        assert f"target_id = aws_organizations_organizational_unit.{ou}.id" in guard
        assert "policy_id = aws_organizations_policy.protect_security_controls.id" in guard


def test_security_delegation_is_opt_in_and_account_scoped():
    for kind in ["aws_guardduty_organization_admin_account", "aws_securityhub_organization_admin_account"]:
        body = resource("organization/delegated-admin.tf", kind, "security")
        assert "count = var.configure_delegated_admins ? 1 : 0" in body
        assert "admin_account_id = local.account_ids.security" in body


def test_organization_trail_delivers_validated_encrypted_management_events():
    trail = resource("audit-trail/main.tf", "aws_cloudtrail", "organization")
    for flag in ["is_multi_region_trail", "is_organization_trail", "enable_log_file_validation",
                 "enable_logging", "include_management_events", "include_global_service_events"]:
        assert f"{flag} = true" in trail
    assert "kms_key_id = var.log_archive_kms_key_arn" in trail
    assert "s3_bucket_name = var.log_archive_bucket_name" in trail


def test_identity_center_admin_assignment_is_limited_to_security_group_and_account():
    path = "identity-center/main.tf"
    admin = resource(path, "aws_ssoadmin_account_assignment", "security_admin")
    assert "principal_id = var.admin_group_id" in admin
    assert "target_id = var.account_ids.security" in admin
    for name in ["readonly", "platform", "security_admin"]:
        assignment = resource(path, "aws_ssoadmin_account_assignment", name)
        expected = "administrator" if name == "security_admin" else name
        assert f"permission_set_arn = aws_ssoadmin_permission_set.{expected}.arn" in assignment
        assert 'principal_type = "GROUP"' in assignment
    for name, policy in [("readonly", "ReadOnlyAccess"), ("platform", "PowerUserAccess"), ("administrator", "AdministratorAccess")]:
        attachment = resource(path, "aws_ssoadmin_managed_policy_attachment", name)
        assert f'managed_policy_arn = "arn:aws:iam::aws:policy/{policy}"' in attachment


def test_dashboard_get_requires_cognito_and_imported_findings_feed_triage():
    method = resource("workload/api.tf", "aws_api_gateway_method", "get")
    assert 'authorization = "COGNITO_USER_POOLS"' in method
    assert "authorizer_id = aws_api_gateway_authorizer.cognito.id" in method
    rule = resource("security-admin/ai-operations.tf", "aws_cloudwatch_event_rule", "securityhub_findings")
    assert 'source = ["aws.securityhub"]' in rule
    assert '"detail-type" = ["Security Hub Findings - Imported"]' in rule

def test_security_investigation_dlq_notifies_on_first_visible_message():
    queue = resource("security-admin/ai-operations.tf", "aws_sqs_queue", "ai_incident_dlq")
    alarm = resource("security-admin/observability.tf", "aws_cloudwatch_metric_alarm", "ai_incident_dlq_visible")

    assert "message_retention_seconds = 1209600" in queue
    assert "sqs_managed_sse_enabled = true" in queue
    assert 'metric_name = "ApproximateNumberOfMessagesVisible"' in alarm
    assert 'namespace = "AWS/SQS"' in alarm
    assert "dimensions = { QueueName = aws_sqs_queue.ai_incident_dlq.name }" in alarm
    assert 'comparison_operator = "GreaterThanOrEqualToThreshold"' in alarm
    assert "threshold = 1" in alarm
    assert "evaluation_periods = 1" in alarm
    assert "period = 60" in alarm
    assert 'statistic = "Maximum"' in alarm
    assert 'treat_missing_data = "notBreaching"' in alarm
    assert "alarm_actions = compact([var.security_alert_topic_arn])" in alarm
