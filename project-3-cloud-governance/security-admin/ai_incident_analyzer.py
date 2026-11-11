import hashlib
import json
import os
import re
import urllib.request
from datetime import datetime, timezone

import boto3
from incident_replay import process

TABLE = os.environ["INCIDENT_TABLE"]
SECRET_ARN = os.environ["OPENAI_SECRET_ARN"]
MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.5")
TOPIC = os.environ.get("SECURITY_ALERT_TOPIC_ARN", "")
RETENTION_DAYS = max(1, min(int(os.environ.get("RETENTION_DAYS", "180")), 3650))

secrets = boto3.client("secretsmanager")
ddb = boto3.client("dynamodb")
sns = boto3.client("sns")
cw = boto3.client("cloudwatch")

_REDACTION_PATTERNS = [
    (re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"), "[REDACTED_AWS_ACCESS_KEY]"),
    (re.compile(r"(?i)\b(authorization\s*[:=]\s*(?:bearer\s+)?)[^\s,;]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)\b(password|passwd|secret|token|api[_-]?key)\s*[:=]\s*[^\s,;]+"), r"\1=[REDACTED]"),
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[REDACTED_EMAIL]"),
    (re.compile(r"(?<!\d)\d{12}(?!\d)"), "[REDACTED_ACCOUNT_ID]"),
]


def _redact(value):
    if isinstance(value, list):
        return [_redact(item) for item in value]
    if isinstance(value, dict):
        return {key: _redact(item) for key, item in value.items()}
    if isinstance(value, str):
        result = value
        for pattern, replacement in _REDACTION_PATTERNS:
            result = pattern.sub(replacement, result)
        return result
    return value


def _key():
    raw = secrets.get_secret_value(SecretId=SECRET_ARN)["SecretString"]
    try:
        obj = json.loads(raw)
        return obj.get("api_key") or obj.get("OPENAI_API_KEY") or raw
    except json.JSONDecodeError:
        return raw


def _text(payload):
    for item in payload.get("output", []):
        for part in item.get("content", []):
            if part.get("type") == "output_text":
                return part.get("text", "")
    raise ValueError("missing output_text")


def _stable_identifier(value):
    raw = str(value or "").strip()
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16] if raw else ""


def _evidence(finding):
    resource = (finding.get("Resources") or [{}])[0]
    def allowed(value, choices):
        return value if value in choices else "unknown"

    severity = finding.get("Severity") or {}
    normalized = str(severity.get("Normalized", ""))
    return {
        "finding_ref": _stable_identifier(finding.get("Id")),
        "product": allowed(finding.get("ProductName"), ("GuardDuty", "Security Hub", "Inspector", "Macie", "Config")),
        "severity": {
            "Label": allowed(severity.get("Label"), ("INFORMATIONAL", "LOW", "MEDIUM", "HIGH", "CRITICAL")),
            "Normalized": int(normalized) if normalized.isascii() and normalized.isdigit()
                          and len(normalized) <= 3 and int(normalized) <= 100 else None,
        },
        "workflow": allowed((finding.get("Workflow") or {}).get("Status"), ("NEW", "NOTIFIED", "RESOLVED", "SUPPRESSED")),
        "record_state": allowed(finding.get("RecordState"), ("ACTIVE", "ARCHIVED")),
        "resource": {
            "type": allowed(resource.get("Type"), ("AwsIamRole", "AwsIamUser", "AwsEc2Instance", "AwsS3Bucket",
                                                   "AwsEc2SecurityGroup", "AwsLambdaFunction", "AwsRdsDbInstance")),
            "resource_ref": _stable_identifier(resource.get("Id")),
        },
    }


def _validate(output):
    required = [
        "summary",
        "triage_priority",
        "likely_cause",
        "business_impact",
        "recommended_checks",
        "evidence_used",
        "confidence",
    ]
    if not isinstance(output, dict) or any(key not in output for key in required):
        raise ValueError("invalid schema")
    if output["triage_priority"] not in {"P1", "P2", "P3", "P4"}:
        raise ValueError("invalid triage priority")
    if output["confidence"] not in {"low", "medium", "high"}:
        raise ValueError("invalid confidence")
    if not isinstance(output["recommended_checks"], list) or not isinstance(output["evidence_used"], list):
        raise ValueError("invalid arrays")
    return output




_PRIORITY_RANK = {"P1": 1, "P2": 2, "P3": 3, "P4": 4}


def _severity_priority(evidence):
    severity = evidence.get("severity", {}) or {}
    normalized = severity.get("Normalized")
    try:
        normalized = float(normalized)
    except (TypeError, ValueError):
        normalized = None

    if normalized is not None:
        if normalized >= 90:
            return "P1"
        if normalized >= 70:
            return "P2"
        if normalized >= 40:
            return "P3"
        return "P4"

    label = str(severity.get("Label", "")).upper()
    return {
        "CRITICAL": "P1",
        "HIGH": "P2",
        "MEDIUM": "P3",
        "LOW": "P4",
        "INFORMATIONAL": "P4",
    }.get(label, "P4")


def _enforce_severity_floor(analysis, evidence):
    floor = _severity_priority(evidence)
    current = analysis["triage_priority"]
    if _PRIORITY_RANK[current] > _PRIORITY_RANK[floor]:
        guarded = dict(analysis)
        guarded["model_triage_priority"] = current
        guarded["triage_priority"] = floor
        guarded["priority_guardrail"] = "security_hub_severity_floor"
        return guarded
    return analysis


def _analyze(evidence):
    body = {
        "model": MODEL,
        "instructions": (
            "Act as a senior cloud security triage assistant. Use only supplied Security Hub evidence. "
            "Do not invent telemetry and do not execute or recommend automatic remediation. Return JSON only "
            "with summary, triage_priority(P1-P4), likely_cause, business_impact, recommended_checks(array), "
            "evidence_used(array), confidence(low|medium|high)."
        ),
        "input": json.dumps(evidence, separators=(",", ":"), default=str),
        "store": False,
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {_key()}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        return _validate(json.loads(_text(json.loads(response.read().decode()))))


def _fallback(evidence, error):
    priority = _severity_priority(evidence)
    return {
        "summary": "AI triage unavailable; review the Security Hub finding directly.",
        "triage_priority": priority,
        "likely_cause": "Undetermined",
        "business_impact": "Undetermined",
        "recommended_checks": ["Review the full Security Hub finding and linked AWS resource evidence."],
        "evidence_used": ["Sanitized Security Hub finding metadata"],
        "confidence": "low",
        "analysis_error": _redact(str(error))[:300],
    }


def handler(event, context):
    findings = (event.get("detail") or {}).get("findings")
    if not isinstance(findings, list) or len(findings) != 1 or not isinstance(findings[0], dict):
        raise ValueError("Expected one Security Hub finding per imported event")
    finding = findings[0]
    raw_id = finding.get("Id")
    if not isinstance(raw_id, str) or not raw_id.strip():
        raise ValueError("Security Hub finding requires an Id")
    finding_id = hashlib.sha256(raw_id.encode()).hexdigest()
    evidence = _evidence(finding)
    closed = evidence["workflow"] in {"RESOLVED", "SUPPRESSED"}
    # NEW and NOTIFIED are the same actionable episode.
    material = dict(evidence, workflow=evidence["workflow"] if closed else "open")
    signature = hashlib.sha256(json.dumps(material, sort_keys=True).encode()).hexdigest()
    observed = _observed_time(finding.get("UpdatedAt"), event.get("time"))
    envelope_order = _observed_time(event.get("time"), finding.get("UpdatedAt"))
    receipt = {"finding_id": {"S": "replay#" + finding_id}}

    def handle_change():
        now = datetime.now(timezone.utc)
        expiry = {"N": str(int(now.timestamp()) + RETENTION_DAYS * 86400)}
        # No record_type: the source locator is excluded from the dashboard index.
        locator_key = "source#" + finding_id
        ddb.put_item(TableName=TABLE, Item={
            "finding_id": {"S": locator_key}, "source_id": {"S": raw_id},
            "product_arn": {"S": finding.get("ProductArn") or ""},
            "region": {"S": finding.get("Region") or event.get("region") or ""},
            "expires_at": expiry,
        })
        if closed:
            # A closure may precede the first investigation. Keep the replay
            # checkpoint, but do not invent a dashboard incident without analysis.
            try:
                ddb.update_item(TableName=TABLE, Key={"finding_id": {"S": finding_id}},
                                ConditionExpression="attribute_exists(finding_id)",
                                UpdateExpression="SET workflow_status = :status, updated_at = :now, "
                                                 "record_type = :kind, expires_at = :expiry",
                                ExpressionAttributeValues={":status": {"S": evidence["workflow"]},
                                                           ":now": {"S": now.isoformat()},
                                                           ":kind": {"S": "incident"}, ":expiry": expiry})
            except ddb.exceptions.ConditionalCheckFailedException:
                pass
            return {"finding_id": finding_id, "status": evidence["workflow"]}, None
        return _investigate(finding_id, evidence, locator_key)

    result = process(ddb, TABLE, receipt, signature, observed, RETENTION_DAYS,
                     handle_change, sns.publish, cancel_pending=closed, event_order=envelope_order)
    return {"statusCode": 200, "body": json.dumps([result])}


def _observed_time(updated, envelope):
    for raw in (updated, envelope):
        if isinstance(raw, str):
            try:
                value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                if value.tzinfo is not None:
                    return value.timestamp()
            except ValueError:
                continue
    if updated is not None or envelope is not None:
        raise ValueError("No valid timezone-aware finding or event timestamp")
    return 0  # Untimed local exercise inputs sort before dated updates.


def _metric(name):
    try:
        cw.put_metric_data(
            Namespace="RSVP/AIOperations",
            MetricData=[{"MetricName": name, "Value": 1, "Dimensions": [{"Name": "FunctionName", "Value": os.environ["AWS_LAMBDA_FUNCTION_NAME"]}], "Unit": "Count"}],
        )
    except Exception:
        # Metrics are observability-only and must not turn a completed triage into a retry.
        pass


def _investigate(finding_id, evidence, locator_key):
    try:
        analysis = _enforce_severity_floor(_analyze(evidence), evidence)
        status = "ai_generated"
    except Exception as exc:
        analysis = _fallback(evidence, exc)
        status = "fallback"

    _metric("SecurityFindingsAnalyzed")
    if status == "fallback":
        _metric("AnalysisFallback")

    now_dt = datetime.now(timezone.utc)
    now = now_dt.isoformat()
    expires_at = int(now_dt.timestamp()) + RETENTION_DAYS * 86400
    ddb.put_item(
        TableName=TABLE,
        Item={
            "finding_id": {"S": finding_id},
            "record_type": {"S": "incident"},
            "updated_at": {"S": now},
            "analysis_status": {"S": status},
            "workflow_status": {"S": evidence["workflow"]},
            "priority": {"S": analysis["triage_priority"]},
            "confidence": {"S": analysis["confidence"]},
            "evidence": {"S": json.dumps(evidence, default=str)},
            "analysis": {"S": json.dumps(analysis, default=str)},
            "expires_at": {"N": str(expires_at)},
        },
    )
    result = {"finding_id": finding_id, "status": status, "priority": analysis["triage_priority"]}

    notification = None
    if TOPIC and analysis["triage_priority"] in {"P1", "P2"}:
        notification = dict(
            TopicArn=TOPIC,
            Subject=f"[RSVP Security] {analysis['triage_priority']} {evidence['product']} finding"[:100],
            Message=json.dumps({"source_record": {"table": TABLE, "finding_id": locator_key},
                                "evidence": evidence, "analysis": analysis}, indent=2, default=str),
        )
    return result, notification
