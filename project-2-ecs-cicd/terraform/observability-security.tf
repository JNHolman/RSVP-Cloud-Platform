data "aws_caller_identity" "current" {}

##############################################
# Central observability encryption
##############################################
resource "aws_kms_key" "observability" {
  description             = "KMS key for RSVP ECS operational CloudWatch logs"
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
      },
      {
        Sid       = "AllowSNSDataKeyUse"
        Effect    = "Allow"
        Principal = { Service = "sns.amazonaws.com" }
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey*",
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "kms:EncryptionContext:aws:sns:topicArn" = "arn:aws:sns:${var.aws_region}:${data.aws_caller_identity.current.account_id}:${local.name_prefix}-operations"
          }
        }
      },
      {
        Sid       = "AllowCloudWatchAlarmPublish"
        Effect    = "Allow"
        Principal = { Service = "cloudwatch.amazonaws.com" }
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey*",
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
          ArnLike = {
            "aws:SourceArn" = "arn:aws:cloudwatch:${var.aws_region}:${data.aws_caller_identity.current.account_id}:alarm:*"
          }
        }
      }
    ]
  })

  tags = { Name = "${local.name_prefix}-observability-kms" }
}

resource "aws_kms_alias" "observability" {
  name          = "alias/${local.name_prefix}-observability"
  target_key_id = aws_kms_key.observability.key_id
}

##############################################
# ALB access logs
##############################################
resource "aws_s3_bucket" "alb_access_logs" {
  #checkov:skip=CKV_AWS_18:This bucket is the dedicated ALB access-log destination; recursively logging a log destination is not recommended by AWS.
  #checkov:skip=CKV_AWS_145:Legacy ALB access-log destinations support SSE-S3, not SSE-KMS; the bucket is private, TLS-only, versioned, and dedicated to ALB logs.
  bucket = "${local.name_prefix}-alb-logs-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_versioning" "alb_access_logs" {
  bucket = aws_s3_bucket.alb_access_logs.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_ownership_controls" "alb_access_logs" {
  bucket = aws_s3_bucket.alb_access_logs.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "alb_access_logs" {
  bucket                  = aws_s3_bucket.alb_access_logs.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "alb_access_logs" {
  bucket = aws_s3_bucket.alb_access_logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "alb_access_logs" {
  bucket = aws_s3_bucket.alb_access_logs.id

  rule {
    id     = "expire-access-logs"
    status = "Enabled"

    filter {}

    expiration {
      days = 180
    }

    noncurrent_version_expiration {
      noncurrent_days = 180
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

data "aws_iam_policy_document" "alb_access_logs" {
  statement {
    sid     = "AllowElasticLoadBalancingLogDelivery"
    effect  = "Allow"
    actions = ["s3:PutObject"]

    principals {
      type        = "Service"
      identifiers = ["logdelivery.elasticloadbalancing.amazonaws.com"]
    }

    resources = ["${aws_s3_bucket.alb_access_logs.arn}/AWSLogs/${data.aws_caller_identity.current.account_id}/*"]

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }

    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = ["arn:aws:elasticloadbalancing:${var.aws_region}:${data.aws_caller_identity.current.account_id}:loadbalancer/*"]
    }
  }

  statement {
    sid     = "DenyInsecureTransport"
    effect  = "Deny"
    actions = ["s3:*"]

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    resources = [
      aws_s3_bucket.alb_access_logs.arn,
      "${aws_s3_bucket.alb_access_logs.arn}/*",
    ]

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket_policy" "alb_access_logs" {
  bucket = aws_s3_bucket.alb_access_logs.id
  policy = data.aws_iam_policy_document.alb_access_logs.json
}

##############################################
# VPC Flow Logs
##############################################
resource "aws_cloudwatch_log_group" "vpc_flow" {
  name              = "/${local.name_prefix}/vpc-flow"
  retention_in_days = 90
  kms_key_id        = aws_kms_key.observability.arn
}

data "aws_iam_policy_document" "vpc_flow_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["vpc-flow-logs.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }

    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = ["arn:aws:ec2:${var.aws_region}:${data.aws_caller_identity.current.account_id}:vpc-flow-log/*"]
    }
  }
}

resource "aws_iam_role" "vpc_flow" {
  name               = "${local.name_prefix}-vpc-flow-logs"
  assume_role_policy = data.aws_iam_policy_document.vpc_flow_assume.json
}

data "aws_iam_policy_document" "vpc_flow" {
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:DescribeLogGroups",
      "logs:DescribeLogStreams",
      "logs:PutLogEvents",
    ]
    resources = ["${aws_cloudwatch_log_group.vpc_flow.arn}:*"]
  }
}

resource "aws_iam_role_policy" "vpc_flow" {
  name   = "publish-vpc-flow-logs"
  role   = aws_iam_role.vpc_flow.id
  policy = data.aws_iam_policy_document.vpc_flow.json
}

resource "aws_flow_log" "vpc" {
  iam_role_arn             = aws_iam_role.vpc_flow.arn
  log_destination          = aws_cloudwatch_log_group.vpc_flow.arn
  log_destination_type     = "cloud-watch-logs"
  max_aggregation_interval = 60
  traffic_type             = "ALL"
  vpc_id                   = aws_vpc.this.id

  depends_on = [aws_iam_role_policy.vpc_flow]
}

##############################################
# WAF request logging
##############################################
resource "aws_cloudwatch_log_group" "waf" {
  name              = "aws-waf-logs-${local.name_prefix}"
  retention_in_days = 90
  kms_key_id        = aws_kms_key.observability.arn
}

resource "aws_wafv2_web_acl_logging_configuration" "app" {
  resource_arn            = aws_wafv2_web_acl.app.arn
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
