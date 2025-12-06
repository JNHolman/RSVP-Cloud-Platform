resource "aws_lambda_function" "ai_incident" {
  function_name = "${var.project_name}-ai-incident-reporter"
  role          = aws_iam_role.ai_incident_lambda_role.arn
  handler       = "ai_incident_lambda.handler"
  runtime       = "python3.10"

  # You will create this zip right next to the .py file
  filename         = "${path.module}/ai_incident_lambda.zip"
  source_code_hash = filebase64sha256("${path.module}/ai_incident_lambda.zip")

  timeout = 60
  memory_size = 256

  environment {
    variables = {
      OPENAI_API_KEY    = var.openai_api_key
      ALERT_TOPIC_ARN   = aws_sns_topic.security_alerts.arn
      INCIDENT_TABLE    = aws_dynamodb_table.ai_incidents.name
      PROJECT_NAME      = var.project_name
      APP_REGION        = var.aws_region
    }
  }

  tags = merge(
    var.tags,
    {
      "Component" = "security"
      "Service"   = "AI-Incident-Lambda"
    }
  )
}

# EventBridge rule for GuardDuty findings
resource "aws_cloudwatch_event_rule" "guardduty_findings" {
  name        = "${var.project_name}-guardduty-findings"
  description = "Trigger AI incident reporter on GuardDuty findings"

  event_pattern = <<EOF
{
  "source": ["aws.guardduty"],
  "detail-type": ["GuardDuty Finding"]
}
EOF
}

resource "aws_cloudwatch_event_target" "guardduty_to_lambda" {
  rule      = aws_cloudwatch_event_rule.guardduty_findings.name
  target_id = "ai-incident-lambda"
  arn       = aws_lambda_function.ai_incident.arn
}

resource "aws_lambda_permission" "allow_events_guardduty" {
  statement_id  = "AllowExecutionFromEventBridgeGuardDuty"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ai_incident.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.guardduty_findings.arn
}
