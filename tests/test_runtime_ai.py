import importlib.util
import json
import os
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RecordingClient:
    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        def call(*args, **kwargs):
            self.calls.append((name, args, kwargs))
            if name == "put_item":
                return {}
            if name == "put_object":
                return {}
            if name == "publish":
                return {"MessageId": "test"}
            if name == "put_metric_data":
                return {}
            raise AssertionError(f"Unexpected client call: {name}")

        return call


def _load_module(path, module_name, env):
    old_env = {key: os.environ.get(key) for key in env}
    os.environ.update(env)

    fake_boto3 = types.ModuleType("boto3")
    fake_boto3.client = lambda *args, **kwargs: RecordingClient()
    previous_boto3 = sys.modules.get("boto3")
    sys.modules["boto3"] = fake_boto3

    try:
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        if previous_boto3 is None:
            sys.modules.pop("boto3", None)
        else:
            sys.modules["boto3"] = previous_boto3
        for key, old_value in old_env.items():
            if old_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old_value


def _project1_module():
    return _load_module(
        ROOT / "infrastructure/project-1-cloud-platform/ai_log_summarizer.py",
        "test_project1_ai_log_summarizer",
        {
            "LOG_GROUP_NAME": "/rsvp/test/app",
            "OPENAI_SECRET_ARN": "arn:aws:secretsmanager:us-east-1:111111111111:secret:test",
            "S3_BUCKET": "test-ai-logs",
            "DDB_TABLE": "test-ai-summaries",
            "SNS_TOPIC_ARN": "",
            "AWS_REGION": "us-east-1",
        },
    )


def _security_module(topic=""):
    return _load_module(
        ROOT / "infrastructure/project-3-cloud-governance/security-admin/ai_incident_analyzer.py",
        "test_security_ai_incident_analyzer",
        {
            "INCIDENT_TABLE": "test-incidents",
            "OPENAI_SECRET_ARN": "arn:aws:secretsmanager:us-east-1:111111111111:secret:test",
            "SECURITY_ALERT_TOPIC_ARN": topic,
            "AWS_REGION": "us-east-1",
        },
    )


def _finops_module():
    return _load_module(
        ROOT / "infrastructure/project-3-cloud-governance/finops-ai/cost_analyzer.py",
        "test_finops_cost_analyzer",
        {
            "COST_TABLE": "test-cost-reports",
            "OPENAI_SECRET_ARN": "arn:aws:secretsmanager:us-east-1:111111111111:secret:test",
            "AWS_REGION": "us-east-1",
        },
    )




def _dashboard_module():
    return _load_module(
        ROOT / "infrastructure/project-3-cloud-governance/workload/dashboard_api.py",
        "test_dashboard_api",
        {
            "APP_REGION": "us-east-1",
            "INCIDENTS_TABLE": "test-incidents",
            "COST_SUMMARIES_TABLE": "test-cost-reports",
            "SECURITY_READ_ROLE_ARN": "arn:aws:iam::111111111111:role/security-read",
            "FINOPS_READ_ROLE_ARN": "arn:aws:iam::222222222222:role/finops-read",
            "ALLOWED_ORIGINS": "https://dashboard.example.com",
            "MAX_ITEMS": "50",
        },
    )


def test_project1_ai_dependency_failure_falls_back_and_persists():
    module = _project1_module()
    module.s3_client = RecordingClient()
    module.ddb = RecordingClient()
    module.sns = RecordingClient()
    module.cloudwatch = RecordingClient()
    module._fetch_recent_logs = lambda: ["application error"]

    def fail_ai(_evidence):
        raise RuntimeError("Secrets Manager temporarily unavailable")

    module._call_openai = fail_ai

    result = module.lambda_handler(
        {
            "detail": {
                "alarmName": "rsvp-prod-alb-5xx",
                "state": {"value": "ALARM", "reason": "threshold crossed"},
            }
        },
        None,
    )

    assert result["statusCode"] == 200
    assert json.loads(result["body"])["status"] == "fallback"
    s3_calls = [call for call in module.s3_client.calls if call[0] == "put_object"]
    assert s3_calls
    assert "ServerSideEncryption" not in s3_calls[0][2]
    ddb_calls = [call for call in module.ddb.calls if call[0] == "put_item"]
    assert ddb_calls
    assert ddb_calls[0][2]["Item"]["analysis_status"]["S"] == "fallback"


def test_project1_log_collection_failure_does_not_drop_alarm():
    module = _project1_module()
    module.s3_client = RecordingClient()
    module.ddb = RecordingClient()
    module.sns = RecordingClient()
    module.cloudwatch = RecordingClient()

    def fail_logs():
        raise RuntimeError("CloudWatch Logs unavailable")

    captured = {}

    def analyze(evidence):
        captured.update(evidence)
        return {
            "summary": "Alarm context only",
            "likely_root_cause": "Undetermined",
            "user_impact": "Undetermined",
            "recommended_checks": ["Inspect CloudWatch Logs when available"],
            "evidence_used": ["CloudWatch alarm context"],
            "confidence": "low",
        }

    module._fetch_recent_logs = fail_logs
    module._call_openai = analyze

    result = module.lambda_handler(
        {
            "detail": {
                "alarmName": "rsvp-prod-rds-cpu",
                "state": {"value": "ALARM", "reason": "high cpu"},
            }
        },
        None,
    )

    assert json.loads(result["body"])["status"] == "ai_generated"
    assert captured["logs"] == []
    assert captured["logs_available"] is False
    assert "CloudWatch Logs unavailable" in captured["log_collection_error"]


def test_security_ai_cannot_downgrade_security_hub_critical_severity():
    module = _security_module(topic="arn:aws:sns:us-east-1:111111111111:security-alerts")
    module.ddb = RecordingClient()
    module.sns = RecordingClient()
    module.cw = RecordingClient()
    module._analyze = lambda _evidence: {
        "summary": "Model under-classified the finding",
        "triage_priority": "P4",
        "likely_cause": "Unknown",
        "business_impact": "Unknown",
        "recommended_checks": ["Review finding"],
        "evidence_used": ["Security Hub finding"],
        "confidence": "low",
    }

    result = module.handler(
        {
            "detail": {
                "findings": [
                    {
                        "Id": "finding-123",
                        "Title": "Critical test finding",
                        "Severity": {"Normalized": 95, "Label": "CRITICAL"},
                        "Resources": [{"Type": "AwsEc2Instance", "Id": "i-test", "Region": "us-east-1"}],
                    }
                ]
            }
        },
        None,
    )

    body = json.loads(result["body"])
    assert body[0]["priority"] == "P1"
    ddb_calls = [call for call in module.ddb.calls if call[0] == "put_item"]
    assert ddb_calls[0][2]["Item"]["priority"]["S"] == "P1"
    stored_analysis = json.loads(ddb_calls[0][2]["Item"]["analysis"]["S"])
    assert stored_analysis["model_triage_priority"] == "P4"
    assert stored_analysis["priority_guardrail"] == "security_hub_severity_floor"
    assert any(name == "publish" for name, _, _ in module.sns.calls)


def test_finops_ai_schema_requires_all_contract_fields():
    module = _finops_module()
    valid = {
        "summary": "Costs are stable",
        "anomalies": [],
        "recommendations": [],
        "confidence": "medium",
    }
    assert module._validate_analysis(valid) == valid

    invalid = {
        "recommendations": [],
        "confidence": "medium",
    }
    try:
        module._validate_analysis(invalid)
    except ValueError as exc:
        assert "summary" in str(exc)
    else:
        raise AssertionError("Malformed FinOps analysis was accepted")


def test_dashboard_api_enforces_cors_and_queries_newest_records():
    module = _dashboard_module()

    class Table:
        def query(self, **kwargs):
            assert kwargs == {
                "IndexName": "by_updated_at",
                "KeyConditionExpression": "record_type = :record_type",
                "ExpressionAttributeValues": {":record_type": "incident"},
                "ScanIndexForward": False,
                "Limit": 50,
            }
            return {"Items": [{"finding_id": "finding-1"}]}

    class DDB:
        def Table(self, name):
            assert name == "test-incidents"
            return Table()

    module._assumed_dynamodb = lambda role, session: DDB()
    event = {
        "resource": "/incidents",
        "httpMethod": "GET",
        "headers": {"origin": "https://dashboard.example.com"},
    }
    result = module.handler(event, None)
    assert result["statusCode"] == 200
    assert result["headers"]["Access-Control-Allow-Origin"] == "https://dashboard.example.com"
    assert json.loads(result["body"])["items"] == [{"finding_id": "finding-1"}]

    event["headers"] = {"origin": "https://attacker.example"}
    result = module.handler(event, None)
    assert "Access-Control-Allow-Origin" not in result["headers"]


def test_dashboard_api_dependency_failure_is_sanitized_503():
    module = _dashboard_module()

    def fail_backend(_role, _session):
        raise RuntimeError("sensitive internal role/table detail")

    module._assumed_dynamodb = fail_backend
    result = module.handler(
        {
            "resource": "/cost-summary",
            "httpMethod": "GET",
            "headers": {"origin": "https://dashboard.example.com"},
        },
        None,
    )

    assert result["statusCode"] == 503
    body = json.loads(result["body"])
    assert body == {"message": "Service Unavailable"}
    assert "sensitive" not in result["body"]


def test_dashboard_api_rejects_non_get_before_backend_access():
    module = _dashboard_module()
    module._assumed_dynamodb = lambda *_args: (_ for _ in ()).throw(AssertionError("backend called"))
    result = module.handler(
        {"resource": "/incidents", "httpMethod": "POST", "headers": {}},
        None,
    )
    assert result["statusCode"] == 405


def test_security_fallback_handles_string_severity_and_redacts_error():
    module = _security_module()
    evidence = {
        "severity": {"Normalized": "95", "Label": "CRITICAL"},
        "title": "test",
    }
    fallback = module._fallback(
        evidence,
        RuntimeError("token=super-secret-value account 123456789012"),
    )

    assert fallback["triage_priority"] == "P1"
    assert "super-secret-value" not in fallback["analysis_error"]
    assert "123456789012" not in fallback["analysis_error"]
    assert "[REDACTED]" in fallback["analysis_error"]


def test_security_metric_failure_does_not_retry_completed_triage():
    module = _security_module()
    module.ddb = RecordingClient()
    module.sns = RecordingClient()

    class FailingMetrics(RecordingClient):
        def put_metric_data(self, *args, **kwargs):
            raise RuntimeError("CloudWatch metrics unavailable")

    module.cw = FailingMetrics()
    module._analyze = lambda _evidence: {
        "summary": "Reviewed",
        "triage_priority": "P3",
        "likely_cause": "Unknown",
        "business_impact": "Unknown",
        "recommended_checks": ["Review finding"],
        "evidence_used": ["Security Hub finding"],
        "confidence": "medium",
    }

    result = module.handler(
        {
            "detail": {
                "findings": [
                    {
                        "Id": "finding-metric-test",
                        "Title": "Medium test finding",
                        "Severity": {"Normalized": 50, "Label": "MEDIUM"},
                        "Resources": [{"Type": "AwsEc2Instance", "Id": "i-test", "Region": "us-east-1"}],
                    }
                ]
            }
        },
        None,
    )

    assert result["statusCode"] == 200
    assert json.loads(result["body"])[0]["priority"] == "P3"


def test_finops_fallback_redacts_sensitive_error_text():
    module = _finops_module()
    data = {
        "top_services": [{"service": "Amazon EC2", "cost": 12.34}],
    }
    fallback = module._fallback(
        data,
        RuntimeError("token=super-secret-value account 123456789012 admin@example.com"),
    )

    reason = fallback["fallback_reason"]
    assert "super-secret-value" not in reason
    assert "123456789012" not in reason
    assert "admin@example.com" not in reason
    assert "[REDACTED]" in reason


def test_project1_event_id_preserves_distinct_alarm_occurrences_and_event_log_window():
    module = _project1_module()
    module.s3_client = RecordingClient()
    module.ddb = RecordingClient()
    module.sns = RecordingClient()
    module.cloudwatch = RecordingClient()

    observed_end_ms = []

    def fetch_logs(*, end_ms=None):
        observed_end_ms.append(end_ms)
        return ["same alarm evidence"]

    module._fetch_recent_logs = fetch_logs
    module._call_openai = lambda _evidence: {
        "summary": "Repeated occurrence",
        "likely_root_cause": "Undetermined",
        "user_impact": "Undetermined",
        "recommended_checks": ["Inspect logs"],
        "evidence_used": ["alarm"],
        "confidence": "low",
    }

    base = {
        "time": "2026-10-04T18:30:00Z",
        "detail": {
            "alarmName": "rsvp-prod-alb-5xx",
            "state": {"value": "ALARM", "reason": "threshold crossed"},
        },
    }
    first = module.lambda_handler({**base, "id": "event-1"}, None)
    second = module.lambda_handler({**base, "id": "event-2"}, None)

    first_id = json.loads(first["body"])["id"]
    second_id = json.loads(second["body"])["id"]
    assert first_id != second_id
    assert observed_end_ms == [1791138600000, 1791138600000]


def test_finops_cost_explorer_pagination_is_fully_aggregated():
    module = _finops_module()

    class CostExplorer:
        def __init__(self):
            self.calls = []

        def get_cost_and_usage(self, **kwargs):
            self.calls.append(kwargs)
            if "NextPageToken" not in kwargs:
                return {
                    "ResultsByTime": [{
                        "Groups": [{
                            "Keys": ["Amazon EC2"],
                            "Metrics": {"UnblendedCost": {"Amount": "2.50"}},
                        }]
                    }],
                    "NextPageToken": "page-2",
                }
            assert kwargs["NextPageToken"] == "page-2"
            return {
                "ResultsByTime": [{
                    "Groups": [
                        {
                            "Keys": ["Amazon EC2"],
                            "Metrics": {"UnblendedCost": {"Amount": "1.25"}},
                        },
                        {
                            "Keys": ["Amazon RDS"],
                            "Metrics": {"UnblendedCost": {"Amount": "4.00"}},
                        },
                    ]
                }]
            }

    module.ce = CostExplorer()
    result = module._cost()

    assert len(module.ce.calls) == 2
    assert result["total_cost"] == 7.75
    costs = {item["service"]: item["cost"] for item in result["top_services"]}
    assert costs == {"Amazon RDS": 4.0, "Amazon EC2": 3.75}


def test_security_finding_identity_does_not_collapse_after_account_redaction(monkeypatch):
    module = _security_module(topic="")
    writes = []

    monkeypatch.setattr(module, "_analyze", lambda evidence: {
        "summary": "ok",
        "triage_priority": "P4",
        "likely_cause": "unknown",
        "business_impact": "low",
        "recommended_checks": [],
        "evidence_used": [],
        "confidence": "low",
    })
    monkeypatch.setattr(module.ddb, "put_item", lambda **kwargs: writes.append(kwargs["Item"]))
    monkeypatch.setattr(module.cw, "put_metric_data", lambda **kwargs: None)

    def event(account_id):
        return {
            "detail": {
                "findings": [{
                    "Id": f"arn:aws:securityhub:us-east-1:{account_id}:subscription/test/finding-1",
                    "Title": "Same finding shape",
                    "Severity": {"Label": "LOW"},
                    "RecordState": "ACTIVE",
                    "Resources": [{
                        "Type": "AwsEc2Instance",
                        "Id": f"arn:aws:ec2:us-east-1:{account_id}:instance/i-0123456789abcdef0",
                        "Region": "us-east-1",
                    }],
                }]
            }
        }

    module.handler(event("111111111111"), None)
    module.handler(event("222222222222"), None)

    assert writes[0]["finding_id"]["S"] != writes[1]["finding_id"]["S"]
    assert "111111111111" not in writes[0]["finding_id"]["S"]
    assert "222222222222" not in writes[1]["finding_id"]["S"]
    assert "111111111111" not in writes[0]["evidence"]["S"]
    assert "222222222222" not in writes[1]["evidence"]["S"]
    assert writes[0]["evidence"]["S"] != writes[1]["evidence"]["S"]


def test_security_ai_hashes_external_identifiers_before_model_evidence():
    module = _security_module()
    finding_id = "arn:aws:securityhub:us-east-1:123456789012:subscription/aws-foundational-security-best-practices/v/1.0.0/finding/abc"
    resource_id = "arn:aws:iam::123456789012:role/ProductionAdmin"
    evidence = module._evidence({
        "Id": finding_id,
        "ProductName": "Security Hub",
        "Title": "Example finding",
        "Description": "Example description",
        "Severity": {"Label": "HIGH"},
        "Resources": [{"Type": "AwsIamRole", "Id": resource_id, "Region": "us-east-1"}],
    })
    serialized = json.dumps(evidence)
    assert finding_id not in serialized
    assert resource_id not in serialized
    assert "ProductionAdmin" not in serialized
    assert evidence["finding_ref"]
    assert evidence["resource"]["resource_ref"]
    assert evidence["resource"]["type"] == "AwsIamRole"


def test_ai_records_write_dynamodb_ttl(monkeypatch):
    p1 = _project1_module()
    p1._fetch_recent_logs = lambda **kwargs: []
    p1._call_openai = lambda evidence: {
        "summary": "ok", "likely_root_cause": "unknown", "user_impact": "none",
        "recommended_checks": [], "evidence_used": [], "confidence": "low",
    }
    p1.s3_client = RecordingClient(); p1.ddb = RecordingClient(); p1.sns = RecordingClient(); p1.cloudwatch = RecordingClient()
    p1.lambda_handler({"id": "event-1", "detail": {"alarmName": "a", "state": {"value": "OK"}}}, None)
    p1_item = next(c for c in p1.ddb.calls if c[0] == "put_item")[2]["Item"]
    assert int(p1_item["expires_at"]["N"]) > 0

    security = _security_module()
    monkeypatch.setattr(security, "_analyze", lambda evidence: {
        "summary": "ok", "triage_priority": "P4", "likely_cause": "unknown",
        "business_impact": "low", "recommended_checks": [], "evidence_used": [], "confidence": "low",
    })
    security.ddb = RecordingClient(); security.sns = RecordingClient(); security.cw = RecordingClient()
    security.handler({"detail": {"findings": [{"Id": "f-1", "Severity": {"Label": "LOW"}, "Resources": []}]}}, None)
    sec_item = next(c for c in security.ddb.calls if c[0] == "put_item")[2]["Item"]
    assert int(sec_item["expires_at"]["N"]) > 0

    finops = _finops_module()
    finops._cost = lambda: {"start_date": "2026-09-27", "end_date": "2026-10-04", "total_cost": 1.0, "top_services": []}
    finops._analyze = lambda data: {"summary": "ok", "anomalies": [], "recommendations": [], "confidence": "low"}
    finops.ddb = RecordingClient(); finops.sns = RecordingClient()
    finops.handler({}, None)
    fin_item = next(c for c in finops.ddb.calls if c[0] == "put_item")[2]["Item"]
    assert int(fin_item["expires_at"]["N"]) > 0
