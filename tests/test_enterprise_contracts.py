from pathlib import Path


def test_dynamodb_runtime_roles_do_not_receive_unnecessary_kms_or_extra_read_permissions():
    security = Path("infrastructure/project-3-cloud-governance/security-admin/ai-operations.tf").read_text()
    finops = Path("infrastructure/project-3-cloud-governance/finops-ai/main.tf").read_text()

    # DynamoDB transparently uses its table encryption key. Application execution
    # roles should be authorized for table API calls, not KMS grant administration.
    for text in (security, finops):
        assert '"kms:CreateGrant"' not in text
        assert 'StringLike = { "kms:ViaService" = "dynamodb.*.amazonaws.com" }' not in text

    # Writers only put records; the cross-account dashboard readers only query them.
    assert '{ Effect = "Allow", Action = ["dynamodb:PutItem"], Resource = aws_dynamodb_table.ai_incidents.arn }' in security
    assert '{ Effect = "Allow", Action = ["dynamodb:PutItem"], Resource = aws_dynamodb_table.cost_reports.arn }' in finops
    assert 'Action   = ["dynamodb:Query"]' in security
    assert 'Action   = ["dynamodb:Query"]' in finops
    assert 'dynamodb:Scan' not in security
    assert 'dynamodb:GetItem' not in security
    assert 'dynamodb:Scan' not in finops
    assert 'dynamodb:GetItem' not in finops


def test_runtime_iam_matches_actual_api_calls():
    p1 = Path("infrastructure/project-1-cloud-platform/iam.tf").read_text()
    finops = Path("infrastructure/project-3-cloud-governance/finops-ai/main.tf").read_text()

    assert 'Action = ["logs:FilterLogEvents"]' in p1
    assert 'logs:GetLogEvents' not in p1
    assert 'logs:DescribeLogStreams' not in p1
    assert 'UseDynamoDbEvidenceKmsKey' not in p1
    assert '"kms:CreateGrant"' not in p1

    assert 'Action = ["ce:GetCostAndUsage"]' in finops
    assert 'ce:GetCostForecast' not in finops


def test_project2_container_base_is_patch_and_distro_pinned():
    dockerfile = Path("infrastructure/project-2-ecs-cicd/app/Dockerfile").read_text()
    assert dockerfile.startswith("FROM python:3.12.15-slim-bookworm\n")
    assert "FROM python:3.12-slim\n" not in dockerfile


def test_release_validator_runs_complete_contract_suite():
    validator = Path("scripts/validate-release.sh").read_text()
    assert "python -m pytest -q -p no:cacheprovider tests" in validator
    assert "tests/test_runtime_ai.py tests/test_infra_contracts.py" not in validator


def test_project1_asg_replacement_can_honor_create_before_destroy():
    ec2 = Path("infrastructure/project-1-cloud-platform/ec2.tf").read_text()
    block = ec2.split('resource "aws_autoscaling_group" "app_asg" {', 1)[1].split('\n}', 1)[0]
    assert 'name_prefix               = "${local.name_prefix}-asg-"' in block
    assert 'create_before_destroy = true' in block
    assert 'name                      = "${local.name_prefix}-asg"' not in block


def test_ci_runs_complete_top_level_contract_suite():
    workflow = Path(".github/workflows/ci.yml").read_text()
    assert "infrastructure/project-2-ecs-cicd/app/tests\n          tests" in workflow
    assert "tests/test_runtime_ai.py\n          tests/test_infra_contracts.py" not in workflow


def test_checkov_retention_exception_is_explicit_and_narrow():
    workflow = Path(".github/workflows/ci.yml").read_text()
    config = Path(".checkov.yml").read_text()
    assert "config_file: .checkov.yml" in workflow
    assert "soft_fail: false" in workflow
    assert "CKV_AWS_338" in config
    assert config.count("CKV_") == 1
    assert "seven years" in config


def test_remote_state_examples_require_customer_managed_kms_key():
    backend_examples = list(Path("infrastructure").glob("**/backend.hcl.example"))
    assert backend_examples
    for path in backend_examples:
        text = path.read_text()
        assert 'encrypt        = true' in text, path
        assert 'kms_key_id     = "REPLACE_WITH_TERRAFORM_STATE_KMS_KEY_ARN"' in text, path


def test_state_bucket_rejects_non_kms_or_wrong_key_writes():
    state = Path("infrastructure/bootstrap-state/main.tf").read_text()
    assert 'sid     = "DenyStateWritesWithoutKMS"' in state
    assert 'variable = "s3:x-amz-server-side-encryption"' in state
    assert 'values   = ["aws:kms"]' in state
    assert 'sid     = "DenyStateWritesWithWrongKMSKey"' in state
    assert 'variable = "s3:x-amz-server-side-encryption-aws-kms-key-id"' in state
    assert 'values   = [aws_kms_key.terraform_state.arn]' in state


def test_dashboard_cors_origin_is_a_single_explicit_https_origin():
    variables = Path("infrastructure/project-3-cloud-governance/workload/variables.tf").read_text()
    assert '^https://[A-Za-z0-9.-]+(:[0-9]{1,5})?$' in variables
    assert '!strcontains(var.dashboard_allowed_origin, "*")' in variables
    assert '!strcontains(var.dashboard_allowed_origin, ",")' in variables
    assert 'wildcards, paths, or multiple origins' in variables


def test_cleanup_docs_do_not_claim_protected_recovery_keys_are_disposable():
    readme = Path("README.md").read_text(encoding="utf-8")
    runbook = Path("docs/DEPLOYMENT.md").read_text(encoding="utf-8")
    assert "Project 1 recovery KMS keys have intentional Terraform destruction guards" in readme
    assert "do not expect an unrestricted `terraform destroy`" in runbook.lower()
    assert "snapshots" in runbook.lower() and "recovery points" in runbook.lower()


def test_workload_stack_has_no_unused_placeholder_app_log_group():
    workload = Path("infrastructure/project-3-cloud-governance/workload")
    terraform = "\n".join(p.read_text(encoding="utf-8") for p in workload.glob("*.tf"))
    assert "workload_app_logs" not in terraform
    assert "/workload/app" not in terraform


def test_project3_runbook_requires_state_kms_backend_placeholder_replacement():
    runbook = Path("docs/DEPLOYMENT.md").read_text(encoding="utf-8")
    project3 = runbook.split("## 3. Bootstrap Project 2 delivery", 1)[0]
    assert "REPLACE_WITH_TERRAFORM_STATE_KMS_KEY_ARN" in project3
    assert "state-bootstrap outputs" in project3


def test_prod_oidc_runbook_requires_github_environment_protection():
    runbook = Path("docs/DEPLOYMENT.md").read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "GitHub Environment protection rules for `prod`" in runbook
    assert "restrict deployment branches/tags" in runbook
    assert "production authorization boundary" in runbook
    assert "GitHub Environment protection rules are an external deployment prerequisite" in readme


def test_project3_project_name_inputs_are_bounded_for_generated_aws_names():
    roots = [
        "organization", "identity-center", "log-archive", "audit-trail",
        "security-admin", "workload", "finops-ai",
    ]
    for root in roots:
        text = Path(f"infrastructure/project-3-cloud-governance/{root}/variables.tf").read_text()
        assert 'project_name must be 1-32 characters' in text, root
        assert '^[a-z0-9]([a-z0-9-]{0,30}[a-z0-9])?$' in text, root


def test_dashboard_cross_account_reader_configuration_cannot_be_half_set():
    for root in ["security-admin", "finops-ai"]:
        prereq = Path(f"infrastructure/project-3-cloud-governance/{root}/prerequisites.tf").read_text()
        variables = Path(f"infrastructure/project-3-cloud-governance/{root}/variables.tf").read_text()
        assert 'dashboard_reader_account_id and dashboard_reader_role_name must either both be set or both be empty.' in prereq
        assert '^[A-Za-z0-9+=,.@_-]{1,64}$' in variables
        assert 'must be empty or a valid SNS topic ARN.' in variables


def test_strict_release_validator_cannot_skip_ci_security_gates_silently():
    script = Path("scripts/validate-release.sh").read_text()
    for gate in ["ruff check", "pip-audit -r", "checkov -d infrastructure", "tflint --init", "trivy image"]:
        assert gate in script, gate
    for message in [
        "Python lint gate not executed",
        "dependency vulnerability audit not executed",
        "IaC security gate not executed",
        "Terraform lint gate not executed",
        "container vulnerability gate not executed",
    ]:
        assert message in script, message


def test_checkov_lambda_exceptions_are_scoped_and_explained():
    lambda_files = {
        "infrastructure/project-1-cloud-platform/ai-logs.tf": ["CKV_AWS_117"],
        "infrastructure/project-3-cloud-governance/security-admin/ai-operations.tf": ["CKV_AWS_117"],
        "infrastructure/project-3-cloud-governance/finops-ai/main.tf": ["CKV_AWS_117"],
        "infrastructure/project-3-cloud-governance/workload/api.tf": ["CKV_AWS_116", "CKV_AWS_117"],
    }
    for path, checks in lambda_files.items():
        text = Path(path).read_text()
        for check in checks:
            assert f"#checkov:skip={check}:" in text, (path, check)
    config = Path(".checkov.yml").read_text()
    assert "CKV_AWS_116" not in config
    assert "CKV_AWS_117" not in config
