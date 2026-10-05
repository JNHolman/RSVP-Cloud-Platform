import json
import os
import re
import urllib.request
from datetime import datetime, timedelta, timezone

import boto3

TABLE = os.environ["COST_TABLE"]
SECRET_ARN = os.environ["OPENAI_SECRET_ARN"]
MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.5")
TOPIC = os.environ.get("ALERT_TOPIC_ARN", "")
RETENTION_DAYS = max(1, min(int(os.environ.get("RETENTION_DAYS", "365")), 3650))

ce = boto3.client("ce", region_name="us-east-1")
secrets = boto3.client("secretsmanager")
ddb = boto3.client("dynamodb")
sns = boto3.client("sns")


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


def _cost():
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=7)
    request = {
        "TimePeriod": {"Start": start.isoformat(), "End": end.isoformat()},
        "Granularity": "DAILY",
        "Metrics": ["UnblendedCost"],
        "GroupBy": [{"Type": "DIMENSION", "Key": "SERVICE"}],
    }

    service_costs = {}
    next_token = None
    while True:
        if next_token:
            request["NextPageToken"] = next_token
        response = ce.get_cost_and_usage(**request)
        for period in response.get("ResultsByTime", []):
            for group in period.get("Groups", []):
                service = group["Keys"][0]
                amount = float(group["Metrics"]["UnblendedCost"]["Amount"])
                service_costs[service] = service_costs.get(service, 0.0) + amount

        new_token = response.get("NextPageToken")
        if not new_token:
            break
        if new_token == next_token:
            raise RuntimeError("Cost Explorer returned a repeated pagination token")
        next_token = new_token

    ranked = sorted(service_costs.items(), key=lambda item: item[1], reverse=True)
    return {
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "total_cost": round(sum(service_costs.values()), 2),
        "top_services": [
            {"service": service, "cost": round(cost, 2)}
            for service, cost in ranked[:10]
        ],
    }


def _validate_analysis(out):
    if not isinstance(out, dict):
        raise TypeError("invalid schema")
    if not isinstance(out.get("summary"), str):
        raise TypeError("invalid summary")
    if not isinstance(out.get("anomalies"), list):
        raise TypeError("invalid anomalies")
    if not isinstance(out.get("recommendations"), list):
        raise TypeError("invalid recommendations")
    if out.get("confidence") not in {"low", "medium", "high"}:
        raise ValueError("invalid confidence")
    return out


def _analyze(data):
    body = {
        "model": MODEL,
        "instructions": (
            "Act as a FinOps advisor. Use only supplied Cost Explorer data. Do not invent savings. "
            "Return JSON only with summary, anomalies(array), recommendations(array), "
            "confidence(low|medium|high). Each recommendation must identify supporting evidence "
            "and mark estimates as estimates."
        ),
        "input": json.dumps(data, separators=(",", ":")),
        "store": False,
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {_key()}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        out = json.loads(_text(json.loads(response.read().decode())))
    return _validate_analysis(out)


def _fallback(data, reason):
    top = data.get("top_services", [])
    recommendations = []
    if top:
        leader = top[0]
        recommendations.append(
            {
                "recommendation": f"Review the highest-cost service: {leader['service']}",
                "evidence": f"Seven-day unblended cost: ${leader['cost']:.2f}",
                "estimate": False,
            }
        )
    return {
        "summary": "AI analysis was unavailable; deterministic Cost Explorer evidence is still available.",
        "anomalies": [],
        "recommendations": recommendations,
        "confidence": "low",
        "fallback_reason": _redact_text(reason)[:200],
    }


def handler(event, context):
    data = _cost()
    try:
        analysis = _analyze(data)
    except Exception as exc:  # noqa: BLE001
        analysis = _fallback(data, exc)

    report_id = f"cost-{data['end_date']}"
    now_dt = datetime.now(timezone.utc)
    now = now_dt.isoformat()
    expires_at = int(now_dt.timestamp()) + RETENTION_DAYS * 86400
    ddb.put_item(
        TableName=TABLE,
        Item={
            "report_id": {"S": report_id},
            "record_type": {"S": "weekly_cost"},
            "generated_at": {"S": now},
            "total_cost": {"N": str(data["total_cost"])},
            "cost_data": {"S": json.dumps(data)},
            "analysis": {"S": json.dumps(analysis)},
            "confidence": {"S": analysis["confidence"]},
            "expires_at": {"N": str(expires_at)},
        },
    )

    if TOPIC:
        sns.publish(
            TopicArn=TOPIC,
            Subject=f"[RSVP FinOps] Weekly AWS cost analysis ${data['total_cost']:.2f}"[:100],
            Message=json.dumps({"cost_data": data, "analysis": analysis}, indent=2),
        )

    return {
        "statusCode": 200,
        "body": json.dumps({"report_id": report_id, "total_cost": data["total_cost"]}),
    }
