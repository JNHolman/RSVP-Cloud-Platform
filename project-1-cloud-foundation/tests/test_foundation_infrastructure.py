import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(relative_path):
    return (ROOT / relative_path).read_text()


def test_project1_observability_contract():
    alb = read("project-1-cloud-foundation/terraform/alb.tf")
    logs = read("project-1-cloud-foundation/terraform/observability-security.tf")
    app_logs = read("project-1-cloud-foundation/terraform/ai-logs.tf")

    assert "access_logs {" in alb
    assert 'enable_deletion_protection = var.environment == "prod"' in alb
    assert "drop_invalid_header_fields = true" in alb
    assert 'resource "aws_flow_log" "vpc"' in logs
    assert 'resource "aws_wafv2_web_acl_logging_configuration" "app"' in logs
    assert 'resource "aws_cloudwatch_log_group" "rds_exports"' in logs
    rds = read("project-1-cloud-foundation/terraform/rds.tf")
    assert "aws_cloudwatch_log_group.rds_exports" in rds
    assert "kms_key_id        = aws_kms_key.observability.arn" in app_logs


def test_ec2_requires_imdsv2_detailed_monitoring_and_encrypted_root_volume():
    ec2 = read("project-1-cloud-foundation/terraform/ec2.tf")
    assert 'http_tokens                 = "required"' in ec2
    assert "http_put_response_hop_limit = 1" in ec2
    assert "monitoring {" in ec2
    assert "enabled = true" in ec2
    assert "encrypted             = true" in ec2


def test_project1_two_az_contract_and_instance_refresh():
    variables = read("project-1-cloud-foundation/terraform/variables.tf")
    ec2 = read("project-1-cloud-foundation/terraform/ec2.tf")
    assert "length(var.public_subnet_cidrs) == 2" in variables
    assert "length(var.private_subnet_cidrs) == 2" in variables
    assert "instance_refresh {" in ec2
    assert 'triggers = ["launch_template"]' in ec2


def test_rds_enhanced_monitoring_and_iam_auth_are_enabled():
    rds = read("project-1-cloud-foundation/terraform/rds.tf")
    assert 'resource "aws_iam_role" "rds_monitoring"' in rds
    assert 'monitoring_interval = 60' in rds
    assert 'monitoring_role_arn = aws_iam_role.rds_monitoring.arn' in rds
    assert 'iam_database_authentication_enabled = true' in rds


def test_production_backup_vault_uses_reversible_governance_lock():
    backup = read("project-1-cloud-foundation/terraform/backup.tf")
    assert 'resource "aws_backup_vault_lock_configuration" "production"' in backup
    assert 'count = var.environment == "prod" ? 1 : 0' in backup
    assert 'min_retention_days = 7' in backup
    assert 'max_retention_days = 35' in backup
    assert not any(line.lstrip().startswith('changeable_for_days') for line in backup.splitlines())


def test_project1_ai_dynamodb_kms_permissions_are_runtime_compatible():
    iam = re.sub(r"[ \t]+", " ", read("project-1-cloud-foundation/terraform/iam.tf"))
    assert '"kms:ViaService" = "dynamodb.${var.aws_region}.amazonaws.com"' in iam
    assert '"kms:EncryptionContext:aws:dynamodb:tableName" = aws_dynamodb_table.ai_log_summaries.name' in iam
    assert 'Sid = "DynamoWriteMetadata"' in iam
    assert 'Action = ["dynamodb:PutItem", "dynamodb:UpdateItem"]' in iam
    assert 'Sid = "UseDynamoDbEvidenceKmsKey"' not in iam
    assert '"kms:CreateGrant"' not in iam


def test_project1_recovery_kms_keys_cannot_be_destroyed_with_recovery_data():
    rds = read("project-1-cloud-foundation/terraform/rds.tf")
    backup = read("project-1-cloud-foundation/terraform/backup.tf")

    for content in (rds, backup):
        assert "prevent_destroy = true" in content
        assert "deletion_window_in_days = 30" in content
    assert "skip_final_snapshot       = false" in rds
    assert 'resource "aws_backup_vault_lock_configuration" "production"' in backup


def test_project1_asg_tracks_concrete_launch_template_version():
    ec2 = read("project-1-cloud-foundation/terraform/ec2.tf")
    assert "version = aws_launch_template.app_lt.latest_version" in ec2
    assert 'version = "$Latest"' not in ec2
    assert 'triggers = ["launch_template"]' in ec2


def test_project1_project_name_respects_alb_name_limit():
    variables = read("project-1-cloud-foundation/terraform/variables.tf")
    assert '^[a-z0-9]([a-z0-9-]{0,20}[a-z0-9])?$' in variables
    assert 'project_name must be 1-22 characters' in variables
    assert "32-character limit" in variables


def test_rds_engine_version_description_matches_auto_minor_upgrade_behavior():
    variables = read("project-1-cloud-foundation/terraform/variables.tf")
    rds = read("project-1-cloud-foundation/terraform/rds.tf")
    assert 'MySQL engine major version; AWS-managed minor version upgrades remain enabled' in variables
    assert 'auto_minor_version_upgrade = true' in rds
    assert 'Pinned MySQL engine version' not in variables


def test_rds_recovery_script_returns_actual_recovery_points():
    script = read("project-1-cloud-foundation/validate-rds-recovery.sh")
    assert "sort_by(RecoveryPoints,&CreationDate)[-5:].{Created:CreationDate,Status:Status,ResourceArn:ResourceArn}" in script
    assert ".{Latest:[].{" not in script
    assert "--output json" in script


def test_rds_slow_query_export_is_actually_enabled_without_general_log_noise():
    rds = read("project-1-cloud-foundation/terraform/rds.tf")
    observability = read("project-1-cloud-foundation/terraform/observability-security.tf")
    assert 'name  = "slow_query_log"' in rds
    assert 'value = "1"' in rds
    assert 'name  = "log_output"' in rds
    assert 'value = "FILE"' in rds
    assert '"slowquery"' in rds
    assert '"general"' not in rds
    assert 'toset(["error", "slowquery"])' in observability


def test_rds_waits_for_enhanced_monitoring_role_policy():
    rds = read("project-1-cloud-foundation/terraform/rds.tf")
    assert "aws_iam_role_policy_attachment.rds_monitoring" in rds


def test_backup_selection_waits_for_backup_role_permissions():
    backup = read("project-1-cloud-foundation/terraform/backup.tf")
    block = backup.split('resource "aws_backup_selection" "rds"', 1)[1]
    assert "aws_iam_role_policy_attachment.backup" in block
    assert "aws_iam_role_policy_attachment.backup_restore" in block


def test_project1_rds_engine_contract_matches_mysql_specific_controls():
    variables = read("project-1-cloud-foundation/terraform/variables.tf")
    rds = read("project-1-cloud-foundation/terraform/rds.tf")
    assert 'condition     = var.rds_engine == "mysql"' in variables
    assert 'error_message = "rds_engine must be mysql for this stack."' in variables
    assert 'name  = "slow_query_log"' in rds
    assert 'name  = "log_output"' in rds


def test_project1_first_boot_is_bounded_and_rds_teardown_semantics_are_environment_aware():
    root = Path(__file__).resolve().parents[2]
    ec2 = (root / "project-1-cloud-foundation/terraform/ec2.tf").read_text()
    rds = (root / "project-1-cloud-foundation/terraform/rds.tf").read_text()
    global_cfg = (root / ".checkov.yml").read_text()

    assert "yum update -y" not in ec2
    assert "dnf install -y httpd amazon-cloudwatch-agent" in ec2
    assert 'deletion_protection       = var.environment == "prod"' in rds
    assert "#checkov:skip=CKV_AWS_293:" in rds
    assert 'formatdate("YYYYMMDDhhmmss", timestamp())' in rds
    assert "ignore_changes = [final_snapshot_identifier]" in rds
    assert "CKV_AWS_293" not in global_cfg

def test_project1_failure_and_dlq_alarms_notify_without_waiting_for_two_events():
    monitoring = read("project-1-cloud-foundation/terraform/monitoring.tf")
    ai_logs = read("project-1-cloud-foundation/terraform/ai-logs.tf")
    fallback = monitoring.split('resource "aws_cloudwatch_metric_alarm" "investigation_degraded" {', 1)[1].split("\n}", 1)[0]
    dlq = monitoring.split('resource "aws_cloudwatch_metric_alarm" "ai_analysis_dlq_visible" {', 1)[1].split("\n}", 1)[0]

    assert "threshold           = 1" in fallback
    assert 'metric_name         = "ApproximateNumberOfMessagesVisible"' in dlq
    assert 'namespace           = "AWS/SQS"' in dlq
    assert 'statistic           = "Maximum"' in dlq
    assert 'period              = 60' in dlq
    assert 'threshold           = 1' in dlq
    assert 'dimensions          = { QueueName = aws_sqs_queue.ai_analysis_dlq.name }' in dlq
    assert 'alarm_actions       = [aws_sns_topic.alerts.arn]' in dlq
    assert 'dead_letter_config { target_arn = aws_sqs_queue.ai_analysis_dlq.arn }' in ai_logs
    assert 'dead_letter_config { arn = aws_sqs_queue.ai_analysis_dlq.arn }' in ai_logs

def test_rds_ca_downloads_check_reviewed_bundle_digests():
    ec2 = read("project-1-cloud-foundation/terraform/ec2.tf")
    variables = read("project-1-cloud-foundation/terraform/variables.tf")
    docker = read("project-2-ecs-cicd/app/Dockerfile")
    ci = read(".github/workflows/ci.yml")

    assert "b1711d12bae51838581281e23b6cb97b1074016873b4dafc80ed14002462dd77" in ec2
    assert "sha256sum -c -" in ec2
    assert 'condition     = length(local.rds_ca_expected_sha256) == 64' in ec2
    assert 'variable "rds_ca_bundle_sha256"' in variables
    assert "90a6f1a7978a1b1b096dca6c57511ca48d3b8cf052f8e704baf358f34ea2f21b" in docker
    assert "sha256sum -c -" in docker
    assert "b1711d12bae51838581281e23b6cb97b1074016873b4dafc80ed14002462dd77" in ci
    assert "sha256sum -c -" in ci
