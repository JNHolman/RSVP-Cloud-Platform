import os
import json
import boto3
from datetime import datetime, timedelta
import urllib.request
import urllib.error

logs_client = boto3.client("logs")
s3_client = boto3.client("s3")
ddb_client = boto3.client("dynamodb")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
BUCKET_NAME = os.environ.get("BUCKET_NAME")
TABLE_NAME = os.environ.get("TABLE_NAME")


def call_openai_chat(prompt: str) -> str:
    """Call OpenAI Chat Completions using only stdlib HTTP."""
    if not OPENAI_API_KEY:
        return "OPENAI_API_KEY is not set. Cannot call OpenAI."

    url = "https://api.openai.com/v1/chat/completions"

    payload = {
        "model": "gpt-4.1-mini",  # or "gpt-4o-mini" depending on your access
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a senior SRE / Cloud Engineer AI assistant. "
                    "You summarize AWS application logs into clear, concise incident reports."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Summarize these AWS logs in clear plain English. "
                    "Explain what happened, which components are impacted, "
                    "any obvious root cause signals, and recommended next actions.\n\n"
                    f"Logs:\n{prompt}"
                ),
            },
        ],
        "max_tokens": 400,
        "temperature": 0.2,
    }

    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8")
            parsed = json.loads(body)
            return parsed["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        return f"OpenAI HTTP error: {e.code} {e.reason}"
    except Exception as e:
        return f"Error calling OpenAI: {str(e)}"


def fetch_logs() -> str:
    """Fetch last 24h of logs from CloudWatch for a couple of log groups."""
    end = int(datetime.utcnow().timestamp() * 1000)
    start = int((datetime.utcnow() - timedelta(hours=24)).timestamp() * 1000)

    # You can adjust these to match real log groups in your account later
    log_groups = [
        "/aws/ec2/app",
        "/aws/applicationelb/rsvp",
    ]

    collected = []

    for group in log_groups:
        try:
            resp = logs_client.filter_log_events(
                logGroupName=group,
                startTime=start,
                endTime=end,
                limit=100,
            )
            for e in resp.get("events", []):
                msg = e.get("message", "")
                ts = e.get("timestamp", 0)
                collected.append(f"[{group} @ {ts}] {msg}")
        except logs_client.exceptions.ResourceNotFoundException:
            # Log group doesn't exist yet – ignore
            continue
        except Exception as e:
            collected.append(f"[{group}] Error fetching logs: {str(e)}")

    if not collected:
        return "No logs available for the last 24 hours."
    return "\n".join(collected)


def save_summary_to_s3_and_ddb(summary: str) -> str:
    """Write the AI summary to S3 and DynamoDB."""
    now = datetime.utcnow().isoformat()
    key = f"summary-{now}.txt"

    # S3
    s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key=key,
        Body=summary.encode("utf-8"),
        ContentType="text/plain",
    )

    # DynamoDB
    ddb_client.put_item(
        TableName=TABLE_NAME,
        Item={
            "id": {"S": key},
            "summary": {"S": summary},
            "timestamp": {"S": now},
        },
    )

    return key


def lambda_handler(event, context):
    logs_text = fetch_logs()
    summary = call_openai_chat(logs_text)
    key = save_summary_to_s3_and_ddb(summary)

    return {
        "status": "ok",
        "summary_saved": key,
        "preview": summary[:300],
    }

