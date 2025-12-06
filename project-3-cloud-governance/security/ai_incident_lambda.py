import os
import json
import boto3
import urllib.request

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ALERT_TOPIC_ARN = os.environ.get("ALERT_TOPIC_ARN")
INCIDENT_TABLE = os.environ.get("INCIDENT_TABLE")
PROJECT_NAME = os.environ.get("PROJECT_NAME", "rsvp-cloud-governance")
APP_REGION = os.environ.get("APP_REGION", "us-east-1")

sns = boto3.client("sns")
dynamodb = boto3.client("dynamodb")
guardduty = boto3.client("guardduty", region_name=APP_REGION)

def call_openai_guardduty_summary(finding):
    """
    Call OpenAI Chat Completions API to generate an incident summary.
    """

    if not OPENAI_API_KEY:
        # Fail gracefully if no key
        return {
            "summary": "OPENAI_API_KEY not configured; unable to generate AI summary.",
            "root_cause": "Unknown",
            "impacted_resources": [],
            "severity": finding.get("Severity", "Unknown"),
            "recommended_remediation": "Check GuardDuty console for details.",
            "escalation_needed": True,
            "business_impact": "Unknown (no AI key).",
        }

    system_prompt = (
        "You are a senior cloud security engineer. You will be given a raw AWS GuardDuty finding. "
        "Return a concise JSON summary with fields: summary, root_cause, impacted_resources, "
        "severity, recommended_remediation, escalation_needed (true/false), business_impact."
    )

    user_content = json.dumps(finding, default=str)

    body = json.dumps(
        {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "response_format": {"type": "json_object"},
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp_body = resp.read()
            data = json.loads(resp_body.decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            return json.loads(content)
    except Exception as e:
        return {
            "summary": f"Error calling OpenAI: {e}",
            "root_cause": "Unknown",
            "impacted_resources": [],
            "severity": finding.get("Severity", "Unknown"),
            "recommended_remediation": "Check GuardDuty console for details.",
            "escalation_needed": True,
            "business_impact": "Unknown (AI call failed).",
        }


def store_incident(finding_id, finding, ai_summary):
    item = {
        "finding_id": {"S": finding_id},
        "finding_raw": {"S": json.dumps(finding, default=str)},
        "ai_summary": {"S": json.dumps(ai_summary, default=str)},
    }

    dynamodb.put_item(
        TableName=INCIDENT_TABLE,
        Item=item,
    )


def publish_alert(finding, ai_summary):
    title = finding.get("Title", "GuardDuty Finding")
    severity = finding.get("Severity", "Unknown")
    type_ = finding.get("Type", "Unknown")

    subject = f"[{PROJECT_NAME}] GuardDuty Finding (sev {severity}): {title}"

    message = {
        "finding_title": title,
        "guardduty_type": type_,
        "severity": severity,
        "region": finding.get("Region", APP_REGION),
        "ai_summary": ai_summary,
    }

    sns.publish(
        TopicArn=ALERT_TOPIC_ARN,
        Subject=subject[:100],
        Message=json.dumps(message, indent=2, default=str),
    )


def handler(event, context):
    """
    EventBridge → Lambda → OpenAI → DynamoDB + SNS
    Event format: GuardDuty Finding via EventBridge.
    """
    # EventBridge wraps the finding in event["detail"]
    detail = event.get("detail", {})
    finding = detail.get("finding", detail)  # sometimes directly in detail

    # If we have a finding ID, try to refetch full from GuardDuty for robustness
    finding_id = finding.get("Id") or finding.get("id")
    detector_id = None

    if "detectorId" in detail:
        detector_id = detail["detectorId"]

    if detector_id and finding_id:
        try:
            resp = guardduty.get_findings(
                DetectorId=detector_id,
                FindingIds=[finding_id],
            )
            if resp.get("Findings"):
                finding = resp["Findings"][0]
        except Exception:
            # Fallback to event copy
            pass

    # Call OpenAI to get AI incident summary
    ai_summary = call_openai_guardduty_summary(finding or {})

    # Store in DynamoDB
    if finding_id:
        store_incident(finding_id, finding, ai_summary)

    # Send SNS alert
    publish_alert(finding, ai_summary)

    return {
        "statusCode": 200,
        "body": json.dumps(
            {"message": "Processed GuardDuty finding", "finding_id": finding_id},
            default=str,
        ),
    }
