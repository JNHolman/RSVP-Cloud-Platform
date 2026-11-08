variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project_name" {
  description = "Lowercase resource prefix. Length is bounded so generated IAM, Lambda, CloudTrail, WAF, and S3 names remain within AWS service limits."
  type        = string
  default     = "rsvp-enterprise"

  validation {
    condition     = can(regex("^[a-z0-9]([a-z0-9-]{0,30}[a-z0-9])?$", var.project_name))
    error_message = "project_name must be 1-32 characters, use lowercase letters/numbers/hyphens only, and start/end with a letter or number."
  }
}

variable "owner" {
  type    = string
  default = "Josh Holman"
}

variable "trail_name" {
  type    = string
  default = "rsvp-enterprise-organization-trail"
}

variable "log_archive_bucket_name" {
  type = string
}

variable "log_archive_kms_key_arn" {
  type = string
}
