resource "aws_kms_key" "ai_logs" {
  # Explicitly retain account-root administration so IAM policies in this
  # account can delegate key use to approved AWS services and roles.
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "EnableAccountAdministration"
      Effect    = "Allow"
      Principal = { AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root" }
      Action    = "kms:*"
      Resource  = "*"
    }]
  })
  description             = "KMS key for AI operational evidence"
  enable_key_rotation     = true
  deletion_window_in_days = 30
}

resource "aws_kms_alias" "ai_logs" {
  name          = "alias/${local.name_prefix}-ai-logs"
  target_key_id = aws_kms_key.ai_logs.key_id
}

resource "aws_s3_bucket" "ai_logs" {
  bucket = "${local.name_prefix}-ai-logs-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_ownership_controls" "ai_logs" {
  bucket = aws_s3_bucket.ai_logs.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "ai_logs" {
  bucket                  = aws_s3_bucket.ai_logs.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "ai_logs" {
  bucket = aws_s3_bucket.ai_logs.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ai_logs" {
  bucket = aws_s3_bucket.ai_logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.ai_logs.arn
    }
    bucket_key_enabled = true
  }
}

data "aws_iam_policy_document" "ai_logs_bucket" {
  statement {
    sid     = "DenyInsecureTransport"
    effect  = "Deny"
    actions = ["s3:*"]

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    resources = [
      aws_s3_bucket.ai_logs.arn,
      "${aws_s3_bucket.ai_logs.arn}/*",
    ]

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket_policy" "ai_logs" {
  bucket = aws_s3_bucket.ai_logs.id
  policy = data.aws_iam_policy_document.ai_logs_bucket.json
}

resource "aws_s3_bucket_logging" "ai_logs" {
  bucket        = aws_s3_bucket.ai_logs.id
  target_bucket = aws_s3_bucket.alb_access_logs.id
  target_prefix = "s3-access/ai-logs/"

  depends_on = [aws_s3_bucket_policy.alb_access_logs]
}

resource "aws_s3_bucket_lifecycle_configuration" "ai_logs" {
  bucket = aws_s3_bucket.ai_logs.id
  rule {
    id     = "expire-ai-evidence"
    status = "Enabled"

    filter {}

    expiration { days = 90 }
    noncurrent_version_expiration { noncurrent_days = 30 }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

resource "aws_dynamodb_table" "ai_log_summaries" {
  name         = "${local.name_prefix}-ai-log-summaries"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"
  attribute {
    name = "id"
    type = "S"
  }
  point_in_time_recovery { enabled = true }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.ai_logs.arn
  }
}

resource "aws_cloudwatch_log_group" "app_logs" {
  name              = "/${local.name_prefix}/app"
  retention_in_days = 30
  kms_key_id        = aws_kms_key.observability.arn
}

resource "aws_cloudwatch_log_group" "ai_lambda" {
  name              = "/aws/lambda/${local.name_prefix}-ai-log-summarizer"
  retention_in_days = 30
  kms_key_id        = aws_kms_key.observability.arn
}

data "archive_file" "ai_lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/ai_log_summarizer.py"
  output_path = "${path.module}/ai_log_summarizer.zip"
}

resource "aws_sqs_queue" "ai_analysis_dlq" {
  name                      = "${local.name_prefix}-ai-analysis-dlq"
  message_retention_seconds = 1209600
  sqs_managed_sse_enabled   = true
}

resource "aws_lambda_function" "ai_log_summarizer" {
  #checkov:skip=CKV_AWS_117:This function only needs public AWS/OpenAI endpoints; VPC attachment would add NAT dependency without protecting a private data path.
  function_name = "${local.name_prefix}-ai-log-summarizer"
  runtime       = "python3.12"
  handler       = "ai_log_summarizer.lambda_handler"
  role          = aws_iam_role.ai_lambda_role.arn
  filename         = data.archive_file.ai_lambda_zip.output_path
  source_code_hash = data.archive_file.ai_lambda_zip.output_base64sha256
  timeout          = 45
  memory_size      = 256
  reserved_concurrent_executions = 2
  kms_key_arn                    = aws_kms_key.observability.arn

  tracing_config {
    mode = "Active"
  }

  depends_on = [
    aws_cloudwatch_log_group.ai_lambda,
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_iam_role_policy_attachment.lambda_xray,
    aws_iam_role_policy_attachment.ai_lambda_policy_attach,
  ]

  dead_letter_config { target_arn = aws_sqs_queue.ai_analysis_dlq.arn }

  environment {
    variables = {
      LOG_GROUP_NAME   = aws_cloudwatch_log_group.app_logs.name
      OPENAI_SECRET_ARN = var.openai_secret_arn
      OPENAI_MODEL      = var.ai_model
      S3_BUCKET         = aws_s3_bucket.ai_logs.bucket
      DDB_TABLE         = aws_dynamodb_table.ai_log_summaries.name
      SNS_TOPIC_ARN     = aws_sns_topic.alerts.arn
      RETENTION_DAYS    = "90"
    }
  }
}

resource "aws_cloudwatch_event_rule" "ai_alarm_rule" {
  name        = "${local.name_prefix}-ai-alarm-rule"
  description = "Send production alarm state changes for advisory AI analysis"
  event_pattern = jsonencode({
    source = ["aws.cloudwatch"]
    "detail-type" = ["CloudWatch Alarm State Change"]
    detail = {
      alarmName = [
        aws_cloudwatch_metric_alarm.alb_5xx_high.alarm_name,
        aws_cloudwatch_metric_alarm.asg_cpu_high.alarm_name,
        aws_cloudwatch_metric_alarm.rds_cpu_high.alarm_name,
        aws_cloudwatch_metric_alarm.rds_free_storage_low.alarm_name
      ]
    }
  })
}

resource "aws_cloudwatch_event_target" "ai_alarm_target" {
  rule      = aws_cloudwatch_event_rule.ai_alarm_rule.name
  target_id = "ai-log-summarizer"
  arn       = aws_lambda_function.ai_log_summarizer.arn
  retry_policy {
    maximum_event_age_in_seconds = 3600
    maximum_retry_attempts       = 2
  }
  dead_letter_config { arn = aws_sqs_queue.ai_analysis_dlq.arn }
}

resource "aws_lambda_permission" "allow_eventbridge_invoke" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ai_log_summarizer.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.ai_alarm_rule.arn
}


data "aws_iam_policy_document" "ai_analysis_dlq_eventbridge" {
  statement {
    sid     = "AllowEventBridgeToSend"
    effect  = "Allow"
    actions = ["sqs:SendMessage"]

    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }

    resources = [aws_sqs_queue.ai_analysis_dlq.arn]

    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = [aws_cloudwatch_event_rule.ai_alarm_rule.arn]
    }
  }
}

resource "aws_sqs_queue_policy" "ai_analysis_dlq_eventbridge" {
  queue_url = aws_sqs_queue.ai_analysis_dlq.id
  policy    = data.aws_iam_policy_document.ai_analysis_dlq_eventbridge.json
}
