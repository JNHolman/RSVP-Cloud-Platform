import hashlib
import json
import os
import re
import urllib.request
from datetime import datetime, timezone

import boto3

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
    # The model does not need globally unique AWS identifiers. Hash them before
    # external processing so triage keeps correlation without disclosing raw
    # finding/resource ARNs, account paths, or resource names.
    evidence = {
        "finding_ref": _stable_identifier(finding.get("Id")),
        "product": finding.get("ProductName"),
        "title": finding.get("Title"),
        "description": finding.get("Description"),
        "severity": finding.get("Severity", {}),
        "types": finding.get("Types", []),
        "workflow": finding.get("Workflow", {}),
        "record_state": finding.get("RecordState"),
        "resource": {
            "type": resource.get("Type"),
            "resource_ref": _stable_identifier(resource.get("Id")),
            "region": resource.get("Region"),
        },
    }
    return _redact(evidence)


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
        raise TypeError("invalid arrays")
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
    findings = (event.get("detail") or {}).get("findings", [])
    results = []

    for finding in findings[:10]:
        evidence = _evidence(finding)

        # Keep the externally visible/stored evidence redacted, but derive the
        # database identity from the original Security Hub finding ID. Hashing
        # preserves uniqueness across organization accounts without persisting
        # account IDs or raw finding ARNs as the partition key.
        raw_finding_id = str(finding.get("Id") or "").strip()
        identity_source = raw_finding_id or json.dumps(finding, sort_keys=True, default=str)
        finding_id = hashlib.sha256(identity_source.encode("utf-8")).hexdigest()

        try:
            analysis = _enforce_severity_floor(_analyze(evidence), evidence)
            status = "ai_generated"
        except Exception as exc:  # noqa: BLE001
            analysis = _fallback(evidence, exc)
            status = "fallback"

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
                "priority": {"S": analysis["triage_priority"]},
                "confidence": {"S": analysis["confidence"]},
                "evidence": {"S": json.dumps(evidence, default=str)},
                "analysis": {"S": json.dumps(analysis, default=str)},
                "expires_at": {"N": str(expires_at)},
            },
        )
        results.append({"finding_id": finding_id, "status": status, "priority": analysis["triage_priority"]})

        if TOPIC and analysis["triage_priority"] in {"P1", "P2"}:
            sns.publish(
                TopicArn=TOPIC,
                Subject=f"[RSVP Security] {analysis['triage_priority']} {evidence.get('title', 'Finding')}"[:100],
                Message=json.dumps({"evidence": evidence, "analysis": analysis}, indent=2, default=str),
            )

    try:
        cw.put_metric_data(
            Namespace="RSVP/AIOperations",
            MetricData=[{"MetricName": "SecurityFindingsAnalyzed", "Value": len(results), "Unit": "Count"}],
        )
    except Exception:  # noqa: BLE001
        # Metrics are observability-only and must not turn a completed triage into a retry.
        pass  # noqa: S110
    return {"statusCode": 200, "body": json.dumps(results)}
