from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(relative_path):
    return (ROOT / relative_path).read_text()


def test_project2_observability_contract():
    alb = read("project-2-ecs-cicd/terraform/alb.tf")
    logs = read("project-2-ecs-cicd/terraform/observability-security.tf")
    ecs_logs = read("project-2-ecs-cicd/terraform/cloudwatch.tf")

    assert "access_logs {" in alb
    assert 'enable_deletion_protection = var.environment == "prod"' in alb
    assert "drop_invalid_header_fields = true" in alb
    assert 'resource "aws_flow_log" "vpc"' in logs
    assert 'resource "aws_wafv2_web_acl_logging_configuration" "app"' in logs
    assert "kms_key_id        = aws_kms_key.observability.arn" in ecs_logs


def test_project2_ecr_uses_customer_managed_kms_encryption():
    bootstrap = read("project-2-ecs-cicd/bootstrap-delivery/main.tf")
    assert 'resource "aws_kms_key" "ecr"' in bootstrap
    assert 'encryption_type = "KMS"' in bootstrap
    assert 'kms_key         = aws_kms_key.ecr.arn' in bootstrap
    assert 'encryption_type = "AES256"' not in bootstrap


def test_project2_container_image_validation_rejects_all_mutable_tags():
    variables = read("project-2-ecs-cicd/terraform/variables.tf")
    assert '@sha256:[0-9a-fA-F]{64}' in variables
    assert ':[0-9a-fA-F]{40}' in variables
    assert 'mutable tags and non-ECR registries are not allowed' in variables
    assert '!endswith(var.container_image, ":latest")' not in variables


def test_project2_ecs_container_runs_nonroot_with_readonly_root_filesystem():
    ecs = read("project-2-ecs-cicd/terraform/ecs.tf")
    assert 'user      = "app"' in ecs
    assert 'readonlyRootFilesystem = true' in ecs
    assert 'name  = "GUNICORN_CMD_ARGS"' in ecs
    assert 'value = "--worker-tmp-dir /dev/shm"' in ecs
    assert 'sourceVolume  = "tmp"' in ecs
    assert 'containerPath = "/tmp"' in ecs
    assert 'readOnly      = false' in ecs
    assert 'volume {' in ecs
    assert 'name = "tmp"' in ecs


def test_project2_container_image_requires_immutable_ecr_uri():
    variables = read("project-2-ecs-cicd/terraform/variables.tf")
    assert 'dkr\\\\.ecr' in variables
    assert 'amazonaws\\\\.com' in variables
    assert '@sha256:[0-9a-fA-F]{64}' in variables
    assert ':[0-9a-fA-F]{40}' in variables
    assert 'non-ECR registries are not allowed' in variables
    assert '(?:' not in variables


def test_project2_dependencies_reference_published_pinned_versions():
    requirements = read("project-2-ecs-cicd/app/requirements.txt")
    dockerfile = read("project-2-ecs-cicd/app/Dockerfile")
    assert "flask==3.1.3" in requirements.lower()
    assert "gunicorn==26.2.0" in requirements.lower()
    assert "gunicorn==26.2.2" not in requirements.lower()
    assert "pip install --no-cache-dir --upgrade pip" not in dockerfile
    assert "pip install --no-cache-dir -r requirements.txt" in dockerfile


def test_project2_runtime_configuration_is_not_dead_or_overstated():
    app = read("project-2-ecs-cicd/app/app.py")
    ecs = read("project-2-ecs-cicd/terraform/ecs.tf")
    assert 'SERVICE_NAME = os.getenv("SERVICE_NAME", "RSVP Cloud Service")' in app
    assert 'name  = "SERVICE_NAME"' in ecs
    assert "AI-assisted incident analysis" not in app
    assert "CloudWatch metrics, logs, alarms, and SNS alerting" in app


def test_github_deploy_scopes_task_definition_registration_to_environment_family():
    bootstrap = read("project-2-ecs-cicd/bootstrap-delivery/main.tf")
    assert 'sid = "EcsTaskDefinitionRead"' in bootstrap
    assert '"ecs:DescribeTaskDefinition"' in bootstrap
    assert '"ecs:ListTaskDefinitions"' in bootstrap
    assert 'sid     = "EcsTaskDefinitionRegister"' in bootstrap
    assert 'actions = ["ecs:RegisterTaskDefinition"]' in bootstrap
    assert 'task-definition/${var.project_name}-${each.key}-task:*' in bootstrap
    register_block = bootstrap.split('sid     = "EcsTaskDefinitionRegister"', 1)[1].split("  }", 1)[0]
    assert 'resources = ["*"]' not in register_block
