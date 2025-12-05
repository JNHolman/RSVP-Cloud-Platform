##############################################
#  AI Log Analysis Storage
##############################################

# S3 bucket for detailed AI summaries
resource "aws_s3_bucket" "ai_logs" {
  bucket = "${local.name_prefix}-ai-logs"

  tags = {
    Name = "${local.name_prefix}-ai-logs"
  }
}

resource "aws_s3_bucket_versioning" "ai_logs_versioning" {
  bucket = aws_s3_bucket.ai_logs.id

  versioning_configuration {
    status = "Enabled"
  }
}

# DynamoDB table for metadata
resource "aws_dynamodb_table" "ai_log_summaries" {
  name         = "${local.name_prefix}-ai-log-summaries"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }

  tags = {
    Name = "${local.name_prefix}-ai-log-summaries"
  }
}

##############################################
#  CloudWatch Log Group (source logs)
##############################################

# You can point this to your app logs (CloudWatch Agent) or ALB logs if you wire them
resource "aws_cloudwatch_log_group" "app_logs" {
  name              = "/${local.name_prefix}/app"
  retention_in_days = 7

  tags = {
    Name = "${local.name_prefix}-app-logs"
  }
}

##############################################
#  Lambda: AI Log Summarizer
##############################################

# Inline Lambda code
locals {
  ai_lambda_code = <<-PY
    import os
    import json
    import time
    import uuid
    import base64
    from datetime import datetime, timedelta, timezone
    import urllib.request

    import boto3

    LOG_GROUP_NAME = os.environ.get("LOG_GROUP_NAME", "")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    S3_BUCKET      = os.environ.get("S3_BUCKET")
    DDB_TABLE      = os.environ.get("DDB_TABLE")
    SNS_TOPIC_ARN  = os.environ.get("SNS_TOPIC_ARN")

    logs_client = boto3.client("logs")
    s3_client   = boto3.client("s3")
    ddb_client  = boto3.client("dynamodb")
    sns_client  = boto3.client("sns")

    def call_openai(summary_prompt):
      url = "https://api.openai.com/v1/chat/completions"
      headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}",
      }
      body = {
        "model": "gpt-4o-mini",
        "messages": [
          {
            "role": "system",
            "content": "You are an SRE assistant. Summarize logs into root-cause style explanations and remediation tips."
          },
          {
            "role": "user",
            "content": summary_prompt
          }
        ],
        "max_tokens": 400,
        "temperature": 0.2
      }

      req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
      with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
      return data["choices"][0]["message"]["content"]

    def fetch_recent_logs():
      if not LOG_GROUP_NAME:
        return []

      # Last 5 minutes of logs
      end = int(time.time() * 1000)
      start = end - (5 * 60 * 1000)

      events = []
      paginator = logs_client.get_paginator("filter_log_events")
      for page in paginator.paginate(
        logGroupName=LOG_GROUP_NAME,
        startTime=start,
        endTime=end,
        limit=200
      ):
        events.extend(page.get("events", []))

      lines = [e.get("message", "") for e in events]
      return lines

    def lambda_handler(event, context):
      alarm_name = None
      new_state  = None
      reason     = None

      detail = event.get("detail", {})
      if detail:
        alarm_name = detail.get("alarmName")
        new_state  = detail.get("state", {}).get("value")
        reason     = detail.get("state", {}).get("reason")

      logs = fetch_recent_logs()
      joined_logs = "\\n".join(logs[:200])

      prompt = (
        f"Alarm: {alarm_name}\\n"
        f"State: {new_state}\\n"
        f"Reason: {reason}\\n"
        "Here are recent logs (may be truncated):\\n"
        f"{joined_logs}\\n\\n"
        "Please summarize likely root cause, impact on users, and recommended next troubleshooting steps."
      )

      try:
        summary = call_openai(prompt)
      except Exception as e:
        summary = f"Failed to call OpenAI: {e}"

      now = datetime.now(timezone.utc).isoformat()
      record_id = str(uuid.uuid4())

      # Save full summary to S3
      s3_key = f"summaries/{record_id}.json"
      s3_body = {
        "id": record_id,
        "timestamp": now,
        "alarm_name": alarm_name,
        "state": new_state,
        "reason": reason,
        "summary": summary,
        "log_lines_sample": logs[:50],
        "raw_event": event,
      }
      s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=s3_key,
        Body=json.dumps(s3_body, default=str).encode("utf-8")
      )

      # Save metadata to DynamoDB
      ddb_client.put_item(
        TableName=DDB_TABLE,
        Item={
          "id": {"S": record_id},
          "timestamp": {"S": now},
          "alarm_name": {"S": alarm_name or "unknown"},
          "state": {"S": new_state or "unknown"},
          "s3_key": {"S": s3_key},
        }
      )

      # Short email summary via SNS
      short_msg = f"[RSVP AI] Alarm {alarm_name} is {new_state}\\n\\n{summary[:600]}"
      if SNS_TOPIC_ARN:
        sns_client.publish(
          TopicArn=SNS_TOPIC_ARN,
          Message=short_msg,
          Subject=f"[RSVP AI] {alarm_name} => {new_state}"
        )

      return {
        "statusCode": 200,
        "body": json.dumps({"id": record_id})
      }
  PY
}

# Write code to a local file that archive_file can zip
resource "local_file" "ai_lambda_py" {
  filename = "${path.module}/ai_log_summarizer.py"
  content  = local.ai_lambda_code
}

data "archive_file" "ai_lambda_zip" {
  type        = "zip"
  source_file = local_file.ai_lambda_py.filename
  output_path = "${path.module}/ai_log_summarizer.zip"
}

resource "aws_lambda_function" "ai_log_summarizer" {
  function_name = "${local.name_prefix}-ai-log-summarizer"
  runtime       = "python3.10"
  handler       = "ai_log_summarizer.lambda_handler"
  role          = aws_iam_role.ai_lambda_role.arn

  filename         = data.archive_file.ai_lambda_zip.output_path
  source_code_hash = data.archive_file.ai_lambda_zip.output_base64sha256

  timeout     = 60
  memory_size = 256

  environment {
    variables = {
      LOG_GROUP_NAME = aws_cloudwatch_log_group.app_logs.name
      OPENAI_API_KEY = var.openai_api_key
      S3_BUCKET      = aws_s3_bucket.ai_logs.bucket
      DDB_TABLE      = aws_dynamodb_table.ai_log_summaries.name
      SNS_TOPIC_ARN  = aws_sns_topic.alerts.arn
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.ai_lambda_policy_attach,
    aws_iam_role_policy_attachment.lambda_basic_execution
  ]
}

##############################################
#  EventBridge Rule: trigger Lambda on alarms
##############################################

resource "aws_cloudwatch_event_rule" "ai_alarm_rule" {
  name        = "${local.name_prefix}-ai-alarm-rule"
  description = "Trigger AI log summarizer on CloudWatch alarm state changes"

  event_pattern = jsonencode({
    "source" : ["aws.cloudwatch"],
    "detail-type" : ["CloudWatch Alarm State Change"],
    "detail" : {
      "alarmName" : [
        aws_cloudwatch_metric_alarm.alb_5xx_high.alarm_name,
        aws_cloudwatch_metric_alarm.asg_cpu_high.alarm_name
      ]
    }
  })
}

resource "aws_cloudwatch_event_target" "ai_alarm_target" {
  rule      = aws_cloudwatch_event_rule.ai_alarm_rule.name
  target_id = "ai-log-summarizer"
  arn       = aws_lambda_function.ai_log_summarizer.arn
}

resource "aws_lambda_permission" "allow_eventbridge_invoke" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ai_log_summarizer.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.ai_alarm_rule.arn
}
