variable "aws_region" {
  type = string
}

variable "project_name" {
  description = "Lowercase resource prefix. Length is bounded so generated IAM, Lambda, API, WAF, and log names remain within AWS service limits."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9]([a-z0-9-]{0,30}[a-z0-9])?$", var.project_name))
    error_message = "project_name must be 1-32 characters, use lowercase letters/numbers/hyphens only, and start/end with a letter or number."
  }
}

variable "environment" {
  type    = string
  default = "prod"

  validation {
    condition     = contains(["dev", "stage", "prod"], var.environment)
    error_message = "environment must be one of: dev, stage, prod."
  }
}

variable "tags" {
  type = map(string)
}

variable "ai_incidents_table_name" {
  type = string

  validation {
    condition     = length(trimspace(var.ai_incidents_table_name)) > 0
    error_message = "ai_incidents_table_name must not be empty."
  }
}

variable "ai_cost_summaries_table_name" {
  type = string

  validation {
    condition     = length(trimspace(var.ai_cost_summaries_table_name)) > 0
    error_message = "ai_cost_summaries_table_name must not be empty."
  }
}

variable "dashboard_allowed_origin" {
  description = "Explicit browser origin allowed to call the dashboard API. Wildcards are intentionally disallowed."
  type        = string

  validation {
    condition = (
      can(regex("^https://[A-Za-z0-9.-]+(:[0-9]{1,5})?$", var.dashboard_allowed_origin)) &&
      !strcontains(var.dashboard_allowed_origin, "*") &&
      !strcontains(var.dashboard_allowed_origin, ",")
    )
    error_message = "dashboard_allowed_origin must be one explicit HTTPS origin (scheme + host + optional port only) and may not contain wildcards, paths, or multiple origins."
  }
}

variable "api_throttle_rate_limit" {
  type    = number
  default = 20
}

variable "api_throttle_burst_limit" {
  type    = number
  default = 40
}

variable "api_rate_limit_per_5m" {
  description = "AWS WAF per-IP request limit evaluated over five minutes."
  type        = number
  default     = 1000
}

variable "security_data_read_role_arn" {
  description = "Cross-account role ARN used by the dashboard Lambda to read security incident data"
  type        = string

  validation {
    condition     = can(regex("^arn:aws[a-z-]*:iam::[0-9]{12}:role/.+", var.security_data_read_role_arn))
    error_message = "security_data_read_role_arn must be a valid IAM role ARN."
  }
}

variable "finops_data_read_role_arn" {
  description = "Cross-account role ARN used by the dashboard Lambda to read FinOps report data"
  type        = string

  validation {
    condition     = can(regex("^arn:aws[a-z-]*:iam::[0-9]{12}:role/.+", var.finops_data_read_role_arn))
    error_message = "finops_data_read_role_arn must be a valid IAM role ARN."
  }
}
