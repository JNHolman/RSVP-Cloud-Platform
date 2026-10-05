data "archive_file" "ai_incident" {
  type        = "zip"
  source_file = "${path.module}/ai_incident_analyzer.py"
  output_path = "${path.module}/ai_incident_analyzer.zip"
}

resource "aws_dynamodb_table" "ai_incidents" {
  name         = "${var.project_name}-ai-security-incidents"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "finding_id"

  attribute {
    name = "finding_id"
    type = "S"
  }

  attribute {
    name = "record_type"
    type = "S"
  }

  attribute {
    name = "updated_at"
    type = "S"
  }

  global_secondary_index {
    name            = "by_updated_at"
    hash_key        = "record_type"
    range_key       = "updated_at"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.observability.arn
  }
}

resource "aws_sqs_queue" "ai_incident_dlq" {
  name                      = "${var.project_name}-ai-security-dlq"
  message_retention_seconds = 1209600
  sqs_managed_sse_enabled   = true
}

resource "aws_iam_role" "ai_incident" {
  name = "${var.project_name}-ai-security-analyzer"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ai_incident_logs" {
  role       = aws_iam_role.ai_incident.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "ai_incident_xray" {
  role       = aws_iam_role.ai_incident.name
  policy_arn = "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess"
}

resource "aws_iam_role_policy" "ai_incident" {
  role = aws_iam_role.ai_incident.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = concat([
      { Effect = "Allow", Action = ["dynamodb:PutItem"], Resource = aws_dynamodb_table.ai_incidents.arn },
      { Effect = "Allow", Action = ["secretsmanager:GetSecretValue"], Resource = var.openai_secret_arn },
      { Effect = "Allow", Action = ["sqs:SendMessage"], Resource = aws_sqs_queue.ai_incident_dlq.arn },
      {
        Effect   = "Allow"
        Action   = ["cloudwatch:PutMetricData"]
        Resource = "*"
        Condition = {
          StringEquals = { "cloudwatch:namespace" = "RSVP/AIOperations" }
        }
      }
    ], var.security_alert_topic_arn == "" ? [] : [
      { Effect = "Allow", Action = ["sns:Publish"], Resource = var.security_alert_topic_arn }
    ])
  })
}

resource "aws_lambda_function" "ai_incident" {
  #checkov:skip=CKV_AWS_117:This function only needs public AWS/OpenAI endpoints; VPC attachment would add NAT dependency without protecting a private data path.
  function_name                  = "${var.project_name}-ai-security-analyzer"
  role                           = aws_iam_role.ai_incident.arn
  runtime                        = "python3.12"
  handler                        = "ai_incident_analyzer.handler"
  filename                       = data.archive_file.ai_incident.output_path
  source_code_hash               = data.archive_file.ai_incident.output_base64sha256
  timeout                        = 45
  memory_size                    = 256
  reserved_concurrent_executions = 3
  kms_key_arn                    = aws_kms_key.observability.arn

  tracing_config {
    mode = "Active"
  }

  depends_on = [
    aws_cloudwatch_log_group.ai_incident,
    aws_iam_role_policy_attachment.ai_incident_logs,
    aws_iam_role_policy_attachment.ai_incident_xray,
    aws_iam_role_policy.ai_incident,
  ]

  dead_letter_config {
    target_arn = aws_sqs_queue.ai_incident_dlq.arn
  }

  environment {
    variables = {
      INCIDENT_TABLE           = aws_dynamodb_table.ai_incidents.name
      OPENAI_SECRET_ARN        = var.openai_secret_arn
      OPENAI_MODEL             = var.ai_model
      SECURITY_ALERT_TOPIC_ARN = var.security_alert_topic_arn
      RETENTION_DAYS           = "180"
    }
  }
}

resource "aws_cloudwatch_event_rule" "securityhub_findings" {
  name = "${var.project_name}-securityhub-ai-triage"
  event_pattern = jsonencode({
    source        = ["aws.securityhub"]
    "detail-type" = ["Security Hub Findings - Imported"]
    detail = {
      findings = {
        RecordState = ["ACTIVE"]
      }
    }
  })
}

resource "aws_cloudwatch_event_target" "securityhub_ai" {
  rule = aws_cloudwatch_event_rule.securityhub_findings.name
  arn  = aws_lambda_function.ai_incident.arn

  retry_policy {
    maximum_event_age_in_seconds = 3600
    maximum_retry_attempts       = 2
  }

  dead_letter_config {
    arn = aws_sqs_queue.ai_incident_dlq.arn
  }
}

data "aws_iam_policy_document" "ai_incident_dlq_eventbridge" {
  statement {
    effect  = "Allow"
    actions = ["sqs:SendMessage"]

    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }

    resources = [aws_sqs_queue.ai_incident_dlq.arn]

    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = [aws_cloudwatch_event_rule.securityhub_findings.arn]
    }
  }
}

resource "aws_sqs_queue_policy" "ai_incident_dlq_eventbridge" {
  queue_url = aws_sqs_queue.ai_incident_dlq.id
  policy    = data.aws_iam_policy_document.ai_incident_dlq_eventbridge.json
}

resource "aws_lambda_permission" "securityhub_events" {
  statement_id  = "AllowSecurityHubEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ai_incident.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.securityhub_findings.arn
}

data "aws_iam_policy_document" "dashboard_read_assume" {
  count = var.dashboard_reader_account_id != "" && var.dashboard_reader_role_name != "" ? 1 : 0

  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    # Trust the workload account rather than a role principal that may not exist yet.
    # The aws:PrincipalArn condition narrows assumption to the exact dashboard role.
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${var.dashboard_reader_account_id}:root"]
    }

    condition {
      test     = "ArnEquals"
      variable = "aws:PrincipalArn"
      values   = ["arn:aws:iam::${var.dashboard_reader_account_id}:role/${var.dashboard_reader_role_name}"]
    }
  }
}

resource "aws_iam_role" "dashboard_read" {
  count = var.dashboard_reader_account_id != "" && var.dashboard_reader_role_name != "" ? 1 : 0

  name               = "${var.project_name}-security-dashboard-read"
  assume_role_policy = data.aws_iam_policy_document.dashboard_read_assume[0].json
}

resource "aws_iam_role_policy" "dashboard_read" {
  count = var.dashboard_reader_account_id != "" && var.dashboard_reader_role_name != "" ? 1 : 0

  name = "read-security-incidents"
  role = aws_iam_role.dashboard_read[0].id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["dynamodb:Query"]
        Resource = [
          aws_dynamodb_table.ai_incidents.arn,
          "${aws_dynamodb_table.ai_incidents.arn}/index/*",
        ]
      },
    ]
  })
}

output "ai_incident_table_name" {
  value = aws_dynamodb_table.ai_incidents.name
}

output "dashboard_read_role_arn" {
  value = var.dashboard_reader_account_id != "" && var.dashboard_reader_role_name != "" ? aws_iam_role.dashboard_read[0].arn : null
}
