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
