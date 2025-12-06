# ─────────────────────────────────────────────
# S3 bucket for Config snapshots
# ─────────────────────────────────────────────
resource "aws_s3_bucket" "config_logs" {
  bucket = "${var.project_name}-config-logs"

  tags = merge(
    var.tags,
    {
      "Component" = "security"
      "Service"   = "Config"
    }
  )
}

resource "aws_s3_bucket_versioning" "config_logs" {
  bucket = aws_s3_bucket.config_logs.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "config_logs" {
  bucket = aws_s3_bucket.config_logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Bucket policy so AWS Config can write to this bucket
data "aws_iam_policy_document" "config_bucket_policy" {
  statement {
    sid    = "AWSConfigBucketPermissionsCheck"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["config.amazonaws.com"]
    }

    actions = [
      "s3:GetBucketAcl",
      "s3:ListBucket"
    ]

    resources = [
      aws_s3_bucket.config_logs.arn
    ]
  }

  statement {
    sid    = "AWSConfigBucketDelivery"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["config.amazonaws.com"]
    }

    actions = [
      "s3:PutObject"
    ]

    resources = [
      "${aws_s3_bucket.config_logs.arn}/*"
    ]
  }
}

resource "aws_s3_bucket_policy" "config_logs" {
  bucket = aws_s3_bucket.config_logs.id
  policy = data.aws_iam_policy_document.config_bucket_policy.json
}

# ─────────────────────────────────────────────
# IAM Role for AWS Config
# ─────────────────────────────────────────────
data "aws_iam_policy_document" "config_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["config.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "config_role" {
  name               = "${var.project_name}-config-role"
  assume_role_policy = data.aws_iam_policy_document.config_assume_role.json

  tags = merge(
    var.tags,
    {
      "Component" = "security"
      "Service"   = "Config"
    }
  )
}

# Inline policy for Config role
data "aws_iam_policy_document" "config_role_policy" {
  statement {
    effect = "Allow"
    actions = [
      "s3:GetBucketAcl",
      "s3:ListBucket",
      "s3:PutObject"
    ]
    resources = [
      aws_s3_bucket.config_logs.arn,
      "${aws_s3_bucket.config_logs.arn}/*"
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "config:*"
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "config_role_inline" {
  name   = "${var.project_name}-config-inline"
  role   = aws_iam_role.config_role.id
  policy = data.aws_iam_policy_document.config_role_policy.json
}

# ─────────────────────────────────────────────
# Config recorder + delivery channel
# ─────────────────────────────────────────────
resource "aws_config_configuration_recorder" "main" {
  name     = "${var.project_name}-recorder"
  role_arn = aws_iam_role.config_role.arn

  recording_group {
    all_supported              = true
    include_global_resource_types = true
  }
}

resource "aws_config_delivery_channel" "main" {
  name           = "${var.project_name}-delivery"
  s3_bucket_name = aws_s3_bucket.config_logs.bucket

  depends_on = [aws_config_configuration_recorder.main]
}

resource "aws_config_configuration_recorder_status" "main" {
  name       = aws_config_configuration_recorder.main.name
  is_enabled = true

  depends_on = [aws_config_delivery_channel.main]
}

# ─────────────────────────────────────────────
# Config Rules
# ─────────────────────────────────────────────

# 1) No public S3 buckets
resource "aws_config_config_rule" "s3_public_read_prohibited" {
  name = "${var.project_name}-s3-public-read-prohibited"

  source {
    owner             = "AWS"
    source_identifier = "S3_BUCKET_PUBLIC_READ_PROHIBITED"
  }

  depends_on = [aws_config_configuration_recorder_status.main]
}

# 2) MFA enabled on root account
resource "aws_config_config_rule" "root_mfa_enabled" {
  name = "${var.project_name}-root-mfa-enabled"

  source {
    owner             = "AWS"
    source_identifier = "ROOT_ACCOUNT_MFA_ENABLED"
  }

  depends_on = [aws_config_configuration_recorder_status.main]
}

# 3) IAM access keys rotated every 90 days
resource "aws_config_config_rule" "iam_access_keys_rotated" {
  name = "${var.project_name}-iam-access-keys-rotated"

  source {
    owner             = "AWS"
    source_identifier = "ACCESS_KEYS_ROTATED"
  }

  input_parameters = jsonencode({
    maxAccessKeyAge = "90"
  })

  depends_on = [aws_config_configuration_recorder_status.main]
}
