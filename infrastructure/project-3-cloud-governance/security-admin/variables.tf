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

variable "openai_secret_arn" {
  description = "Secrets Manager ARN containing the OpenAI API key in the security account"
  type        = string

  validation {
    condition     = can(regex("^arn:aws:secretsmanager:", var.openai_secret_arn))
    error_message = "openai_secret_arn must be an AWS Secrets Manager ARN."
  }
}

variable "ai_model" {
  description = "OpenAI model for advisory security analysis"
  type        = string
  default     = "gpt-5.5"
}

variable "security_alert_topic_arn" {
  description = "SNS topic for security operations notifications; empty disables notifications."
  type        = string
  default     = ""

  validation {
    condition     = var.security_alert_topic_arn == "" || can(regex("^arn:aws[a-z-]*:sns:[a-z0-9-]+:[0-9]{12}:.+$", var.security_alert_topic_arn))
    error_message = "security_alert_topic_arn must be empty or a valid SNS topic ARN."
  }
}

variable "dashboard_reader_account_id" {
  description = "Workload AWS account ID allowed to assume the dashboard read role. Leave empty to disable cross-account dashboard access."
  type        = string
  default     = ""

  validation {
    condition     = var.dashboard_reader_account_id == "" || can(regex("^[0-9]{12}$", var.dashboard_reader_account_id))
    error_message = "dashboard_reader_account_id must be empty or a 12-digit AWS account ID."
  }
}

variable "dashboard_reader_role_name" {
  description = "Exact workload IAM role name allowed to assume the dashboard read role."
  type        = string
  default     = ""

  validation {
    condition     = var.dashboard_reader_role_name == "" || can(regex("^[A-Za-z0-9+=,.@_-]{1,64}$", var.dashboard_reader_role_name))
    error_message = "dashboard_reader_role_name must be empty or a valid IAM role name up to 64 characters."
  }
}
