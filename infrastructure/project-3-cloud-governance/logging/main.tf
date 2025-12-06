locals {
  log_bucket_name = "${var.project_name}-central-logs"
}

resource "aws_s3_bucket" "central_logs" {
  bucket = local.log_bucket_name

  tags = merge(
    var.tags,
    {
      "Component" = "logging"
    }
  )
}

resource "aws_s3_bucket_versioning" "central_logs" {
  bucket = aws_s3_bucket.central_logs.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "central_logs" {
  bucket = aws_s3_bucket.central_logs.id

  rule {
    id     = "expire-old-logs"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    expiration {
      days = 365
    }
  }
}

output "cloudtrail_bucket_arn" {
  description = "ARN of the central logging bucket (for CloudTrail / Config)"
  value       = aws_s3_bucket.central_logs.arn
}
