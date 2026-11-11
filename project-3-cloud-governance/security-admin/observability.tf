data "aws_caller_identity" "current" {}

resource "aws_kms_key" "observability" {
  description             = "KMS key for Security account operational logs"
  enable_key_rotation     = true
  deletion_window_in_days = 30

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "EnableAccountAdministration"
        Effect    = "Allow"
        Principal = { AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root" }
        Action    = "kms:*"
        Resource  = "*"
      },
      {
        Sid       = "AllowLambdaPackageEncryption"
        Effect    = "Allow"
        Principal = { Service = "lambda.amazonaws.com" }
        Action = [
          "kms:GenerateDataKey",
          "kms:Decrypt",
        ]
        Resource = "*"
        Condition = {
          StringLike = {
            "kms:EncryptionContext:aws:lambda:FunctionArn" = "arn:aws:lambda:${var.aws_region}:${data.aws_caller_identity.current.account_id}:function:${var.project_name}-ai-security-analyzer"
          }
        }
      },
      {
        Sid       = "AllowCloudWatchLogs"
        Effect    = "Allow"
        Principal = { Service = "logs.${var.aws_region}.amazonaws.com" }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:Describe*",
        ]
        Resource = "*"
        Condition = {
          ArnLike = {
            "kms:EncryptionContext:aws:logs:arn" = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:*"
          }
        }
      }
    ]
  })
}

resource "aws_kms_alias" "observability" {
  name          = "alias/${var.project_name}-security-observability"
  target_key_id = aws_kms_key.observability.key_id
}

resource "aws_cloudwatch_log_group" "ai_incident" {
  name              = "/aws/lambda/${var.project_name}-ai-security-analyzer"
  retention_in_days = 90
  kms_key_id        = aws_kms_key.observability.arn
}

resource "aws_cloudwatch_metric_alarm" "investigation_degraded" {
  for_each            = toset(["AnalysisFallback"])
  alarm_name          = "${var.project_name}-${each.key}"
  alarm_description   = "One ${each.key} event in 15 minutes. Inspect recent investigation records and the function logs."
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = each.key
  namespace           = "RSVP/AIOperations"
  period              = 900
  statistic           = "Sum"
  threshold           = 1
  treat_missing_data  = "notBreaching"
  dimensions          = { FunctionName = aws_lambda_function.ai_incident.function_name }
  alarm_actions       = compact([var.security_alert_topic_arn])
}

resource "aws_cloudwatch_metric_alarm" "ai_incident_dlq_visible" {
  alarm_name          = "${var.project_name}-ai-security-dlq-visible"
  alarm_description   = "A failed security finding event is waiting in the dead-letter queue. Review and replay before its retention period expires."
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 60
  statistic           = "Maximum"
  threshold           = 1
  treat_missing_data  = "notBreaching"
  dimensions          = { QueueName = aws_sqs_queue.ai_incident_dlq.name }
  alarm_actions       = compact([var.security_alert_topic_arn])
}
