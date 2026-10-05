import hashlib
import json
import os
import re
import time
import urllib.request
from datetime import datetime, timezone

import boto3

LOG_GROUP_NAME = os.environ["LOG_GROUP_NAME"]
OPENAI_SECRET_ARN = os.environ["OPENAI_SECRET_ARN"]
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.5")
S3_BUCKET = os.environ["S3_BUCKET"]
DDB_TABLE = os.environ["DDB_TABLE"]
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN", "")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
RETENTION_DAYS = max(1, min(int(os.environ.get("RETENTION_DAYS", "90")), 3650))

logs_client = boto3.client("logs")
s3_client = boto3.client("s3")
ddb = boto3.client("dynamodb")
sns = boto3.client("sns")
secrets = boto3.client("secretsmanager")
cloudwatch = boto3.client("cloudwatch")


_REDACTION_PATTERNS = [
    (re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"), "[REDACTED_AWS_ACCESS_KEY]"),
    (re.compile(r"(?i)\b(authorization\s*[:=]\s*(?:bearer\s+)?)[^\s,;]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)\b(password|passwd|secret|token|api[_-]?key)\s*[:=]\s*[^\s,;]+"), r"\1=[REDACTED]"),
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[REDACTED_EMAIL]"),
    (re.compile(r"(?<!\d)\d{12}(?!\d)"), "[REDACTED_ACCOUNT_ID]"),
]


def _redact_text(value):
    text = str(value)
    for pattern, replacement in _REDACTION_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _metric(name, value=1):
    try:
        cloudwatch.put_metric_data(
            Namespace="RSVP/AIOperations",
            MetricData=[{"MetricName": name, "Value": value, "Unit": "Count"}],
        )
    except Exception:  # noqa: BLE001
        # Metrics are best-effort telemetry; failure must not break incident processing.
        return


def _get_api_key():
    value = secrets.get_secret_value(SecretId=OPENAI_SECRET_ARN)["SecretString"]
    try:
        parsed = json.loads(value)
        return parsed.get("api_key") or parsed.get("OPENAI_API_KEY") or value
    except json.JSONDecodeError:
        return value


def _extract_output_text(response):
    for item in response.get("output", []):
        if item.get("type") != "message":
            continue
        for part in item.get("content", []):
            if part.get("type") == "output_text" and part.get("text"):
                return part["text"]
    raise ValueError("OpenAI response did not contain output_text")


def _validated_analysis(value):
    required = {
        "summary": str,
        "likely_root_cause": str,
        "user_impact": str,
        "recommended_checks": list,
        "evidence_used": list,
        "confidence": str,
    }
    if not isinstance(value, dict):
        raise TypeError("AI output must be a JSON object")
    for key, expected_type in required.items():
        if key not in value or not isinstance(value[key], expected_type):
            raise ValueError(f"AI output missing/invalid field: {key}")
    if value["confidence"] not in {"low", "medium", "high"}:
        raise ValueError("confidence must be low, medium, or high")
    return value


def _call_openai(evidence):
    api_key = _get_api_key()
    instructions = (
        "You are an SRE incident-analysis assistant. Use only the supplied evidence. "
        "Never claim a root cause as proven unless the evidence proves it. Never recommend destructive "
        "or automatic remediation. Return JSON only with fields summary, likely_root_cause, user_impact, "
        "recommended_checks (array), evidence_used (array), confidence (low|medium|high)."
    )
    body = {
        "model": OPENAI_MODEL,
        "instructions": instructions,
        "input": json.dumps(evidence, separators=(",", ":"), default=str),
        "store": False,
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return _validated_analysis(json.loads(_extract_output_text(payload)))


def _event_time_ms(event):
    raw = event.get("time")
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        return int(parsed.timestamp() * 1000)
    except (TypeError, ValueError):
        return None


def _fetch_recent_logs(minutes=5, max_events=120, end_ms=None):
    end = end_ms if end_ms is not None else int(time.time() * 1000)
    start = end - minutes * 60 * 1000
    events = []
    paginator = logs_client.get_paginator("filter_log_events")
    for page in paginator.paginate(
        logGroupName=LOG_GROUP_NAME,
        startTime=start,
        endTime=end,
        PaginationConfig={"MaxItems": max_events, "PageSize": 100},
    ):
        for event in page.get("events", []):
            message = event.get("message", "")
            # Bound payload and avoid shipping arbitrarily large log lines to an external model.
            events.append(_redact_text(message[:2000]))
            if len(events) >= max_events:
                return events
    return events


def _fallback(reason, evidence):
    return {
        "summary": "AI analysis unavailable; use the captured alarm and log evidence for manual triage.",
        "likely_root_cause": "Undetermined",
        "user_impact": "Undetermined from available evidence",
        "recommended_checks": [
            "Review the triggering CloudWatch alarm state and reason.",
            f"Inspect recent events in {LOG_GROUP_NAME}.",
            "Follow the service runbook before making any production change.",
        ],
        "evidence_used": ["CloudWatch alarm context", f"{len(evidence.get('logs', []))} recent log lines"],
        "confidence": "low",
        "analysis_error": reason[:300],
    }


def lambda_handler(event, context):
    detail = event.get("detail", {}) or {}
    alarm_name = detail.get("alarmName", "unknown")
    state = (detail.get("state") or {}).get("value", "unknown")
    reason = _redact_text((detail.get("state") or {}).get("reason", ""))

    event_time_ms = _event_time_ms(event)
    log_collection_error = ""
    try:
        if event_time_ms is None:
            logs = _fetch_recent_logs()
        else:
            logs = _fetch_recent_logs(end_ms=event_time_ms)
    except Exception as exc:  # noqa: BLE001
        # Alarm context is still useful if CloudWatch Logs is temporarily unavailable.
        # Keep the workflow alive and make the missing evidence explicit.
        logs = []
        log_collection_error = _redact_text(str(exc))[:300]
        _metric("LogCollectionFailure")

    evidence = {
        "alarm_name": alarm_name,
        "alarm_state": state,
        "alarm_reason": reason,
        "event_id": str(event.get("id", "")),
        "event_time": str(event.get("time", "")),
        "log_group": LOG_GROUP_NAME,
        "logs_available": bool(logs),
        "logs": logs,
    }
    if log_collection_error:
        evidence["log_collection_error"] = log_collection_error

    event_id = str(event.get("id", "")).strip()
    fingerprint_source = (
        {"event_id": event_id}
        if event_id
        else {
            "alarm": alarm_name,
            "state": state,
            "reason": reason,
            "event_time": str(event.get("time", "")),
        }
    )
    event_fingerprint = hashlib.sha256(
        json.dumps(fingerprint_source, sort_keys=True).encode("utf-8")
    ).hexdigest()[:32]

    try:
        analysis = _call_openai(evidence)
        analysis_status = "ai_generated"
        _metric("AnalysisSuccess")
    except Exception as exc:  # noqa: BLE001
        # AI is advisory. Secrets Manager, network, model, or schema failures must
        # degrade to deterministic evidence rather than drop the incident record.
        analysis = _fallback(_redact_text(str(exc)), evidence)
        analysis_status = "fallback"
        _metric("AnalysisFallback")

    now_dt = datetime.now(timezone.utc)
    now = now_dt.isoformat()
    expires_at = int(now_dt.timestamp()) + RETENTION_DAYS * 86400
    record = {
        "id": event_fingerprint,
        "timestamp": now,
        "alarm_name": alarm_name,
        "state": state,
        "analysis_status": analysis_status,
        "analysis": analysis,
        "evidence": evidence,
        "guardrail": "advisory_only_no_automatic_remediation",
    }
    key = f"summaries/{event_fingerprint}.json"

    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=json.dumps(record, default=str).encode("utf-8"),
        ContentType="application/json",
    )
    ddb.put_item(
        TableName=DDB_TABLE,
        Item={
            "id": {"S": event_fingerprint},
            "timestamp": {"S": now},
            "alarm_name": {"S": alarm_name},
            "state": {"S": state},
            "analysis_status": {"S": analysis_status},
            "confidence": {"S": analysis.get("confidence", "low")},
            "s3_key": {"S": key},
            "expires_at": {"N": str(expires_at)},
        },
    )

    if SNS_TOPIC_ARN and state == "ALARM":
        message = {
            "alarm": alarm_name,
            "state": state,
            "analysis_status": analysis_status,
            "confidence": analysis.get("confidence"),
            "summary": analysis.get("summary"),
            "recommended_checks": analysis.get("recommended_checks", [])[:5],
            "evidence_record": f"s3://{S3_BUCKET}/{key}",
        }
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=f"[RSVP Ops] {alarm_name} -> {state}"[:100],
            Message=json.dumps(message, indent=2),
        )

    return {"statusCode": 200, "body": json.dumps({"id": event_fingerprint, "status": analysis_status})}
