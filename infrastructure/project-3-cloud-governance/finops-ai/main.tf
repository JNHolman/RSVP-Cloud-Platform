data "archive_file" "cost_analyzer" {
  type        = "zip"
  source_file = "${path.module}/cost_analyzer.py"
  output_path = "${path.module}/cost_analyzer.zip"
}

resource "aws_dynamodb_table" "cost_reports" {
  name         = "${var.project_name}-ai-cost-reports"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "report_id"

  attribute {
    name = "report_id"
    type = "S"
  }

  attribute {
    name = "record_type"
    type = "S"
  }

  attribute {
    name = "generated_at"
    type = "S"
  }

  global_secondary_index {
    name            = "by_generated_at"
    hash_key        = "record_type"
    range_key       = "generated_at"
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

resource "aws_sqs_queue" "dlq" {
  name                      = "${var.project_name}-ai-finops-dlq"
  message_retention_seconds = 1209600
  sqs_managed_sse_enabled   = true
}

resource "aws_iam_role" "lambda" {
  name = "${var.project_name}-ai-finops"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "logs" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "xray" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess"
}

resource "aws_iam_role_policy" "lambda" {
  role = aws_iam_role.lambda.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = concat([
      { Effect = "Allow", Action = ["ce:GetCostAndUsage"], Resource = "*" },
      { Effect = "Allow", Action = ["dynamodb:PutItem"], Resource = aws_dynamodb_table.cost_reports.arn },
      { Effect = "Allow", Action = ["secretsmanager:GetSecretValue"], Resource = var.openai_secret_arn },
      { Effect = "Allow", Action = ["sqs:SendMessage"], Resource = aws_sqs_queue.dlq.arn }
    ], var.alert_topic_arn == "" ? [] : [
      { Effect = "Allow", Action = ["sns:Publish"], Resource = var.alert_topic_arn }
    ])
  })
}

resource "aws_lambda_function" "cost_analyzer" {
  #checkov:skip=CKV_AWS_117:This function only needs public AWS/OpenAI endpoints; VPC attachment would add NAT dependency without protecting a private data path.
  function_name                  = "${var.project_name}-ai-finops-analyzer"
  role                           = aws_iam_role.lambda.arn
  runtime                        = "python3.12"
  handler                        = "cost_analyzer.handler"
  filename                       = data.archive_file.cost_analyzer.output_path
  source_code_hash               = data.archive_file.cost_analyzer.output_base64sha256
  timeout                        = 45
  memory_size                    = 256
  reserved_concurrent_executions = 1
  kms_key_arn                    = aws_kms_key.observability.arn

  tracing_config {
    mode = "Active"
  }

  depends_on = [
    aws_cloudwatch_log_group.cost_analyzer,
    aws_iam_role_policy_attachment.logs,
    aws_iam_role_policy_attachment.xray,
    aws_iam_role_policy.lambda,
  ]

  dead_letter_config {
    target_arn = aws_sqs_queue.dlq.arn
  }

  environment {
    variables = {
      COST_TABLE        = aws_dynamodb_table.cost_reports.name
      OPENAI_SECRET_ARN = var.openai_secret_arn
      OPENAI_MODEL      = var.ai_model
      ALERT_TOPIC_ARN   = var.alert_topic_arn
      RETENTION_DAYS    = "365"
    }
  }
}

resource "aws_cloudwatch_event_rule" "weekly" {
  name                = "${var.project_name}-weekly-ai-finops"
  schedule_expression = "cron(0 12 ? * MON *)"
}

resource "aws_cloudwatch_event_target" "weekly" {
  rule = aws_cloudwatch_event_rule.weekly.name
  arn  = aws_lambda_function.cost_analyzer.arn

  retry_policy {
    maximum_event_age_in_seconds = 3600
    maximum_retry_attempts       = 2
  }

  dead_letter_config {
    arn = aws_sqs_queue.dlq.arn
  }
}

data "aws_iam_policy_document" "dlq_eventbridge" {
  statement {
    effect  = "Allow"
    actions = ["sqs:SendMessage"]

    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }

    resources = [aws_sqs_queue.dlq.arn]

    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = [aws_cloudwatch_event_rule.weekly.arn]
    }
  }
}

resource "aws_sqs_queue_policy" "dlq_eventbridge" {
  queue_url = aws_sqs_queue.dlq.id
  policy    = data.aws_iam_policy_document.dlq_eventbridge.json
}

resource "aws_lambda_permission" "events" {
  statement_id  = "AllowWeeklyFinOps"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cost_analyzer.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.weekly.arn
}

data "aws_iam_policy_document" "dashboard_read_assume" {
  count = var.dashboard_reader_account_id != "" && var.dashboard_reader_role_name != "" ? 1 : 0

  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

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

  name               = "${var.project_name}-finops-dashboard-read"
  assume_role_policy = data.aws_iam_policy_document.dashboard_read_assume[0].json
}

resource "aws_iam_role_policy" "dashboard_read" {
  count = var.dashboard_reader_account_id != "" && var.dashboard_reader_role_name != "" ? 1 : 0

  name = "read-cost-reports"
  role = aws_iam_role.dashboard_read[0].id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["dynamodb:Query"]
        Resource = [
          aws_dynamodb_table.cost_reports.arn,
          "${aws_dynamodb_table.cost_reports.arn}/index/*",
        ]
      },
    ]
  })
}

output "cost_reports_table_name" {
  value = aws_dynamodb_table.cost_reports.name
}

output "dashboard_read_role_arn" {
  value = var.dashboard_reader_account_id != "" && var.dashboard_reader_role_name != "" ? aws_iam_role.dashboard_read[0].arn : null
}
