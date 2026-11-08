data "aws_caller_identity" "current" {}

resource "aws_kms_key" "observability" {
  description             = "KMS key for workload logs and Lambda data"
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
            "kms:EncryptionContext:aws:lambda:FunctionArn" = "arn:aws:lambda:${var.aws_region}:${data.aws_caller_identity.current.account_id}:function:${var.project_name}-${var.environment}-dashboard-api"
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
  name          = "alias/${var.project_name}-${var.environment}-workload-observability"
  target_key_id = aws_kms_key.observability.key_id
}

resource "aws_cloudwatch_log_group" "dashboard_lambda" {
  name              = "/aws/lambda/${var.project_name}-${var.environment}-dashboard-api"
  retention_in_days = 90
  kms_key_id        = aws_kms_key.observability.arn
}

resource "aws_cloudwatch_log_group" "waf" {
  name              = "aws-waf-logs-${var.project_name}-${var.environment}-dashboard"
  retention_in_days = 90
  kms_key_id        = aws_kms_key.observability.arn
}

resource "aws_wafv2_web_acl_logging_configuration" "dashboard_api" {
  resource_arn            = aws_wafv2_web_acl.dashboard_api.arn
  log_destination_configs = [aws_cloudwatch_log_group.waf.arn]

  redacted_fields {
    single_header {
      name = "authorization"
    }
  }

  redacted_fields {
    single_header {
      name = "cookie"
    }
  }
}
