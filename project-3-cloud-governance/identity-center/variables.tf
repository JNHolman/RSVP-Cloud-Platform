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

variable "account_ids" {
  type = object({
    security        = string
    log_archive     = string
    shared_services = string
    nonprod         = string
    prod            = string
  })

  validation {
    condition     = alltrue([for id in values(var.account_ids) : can(regex("^[0-9]{12}$", id))])
    error_message = "Every Identity Center target account must be a 12-digit AWS account ID."
  }
}

variable "admin_group_id" {
  description = "Identity Store group ID for cloud administrators."
  type        = string
  validation {
    condition     = trimspace(var.admin_group_id) != ""
    error_message = "admin_group_id must not be empty."
  }
}

variable "platform_group_id" {
  description = "Identity Store group ID for platform operators."
  type        = string
  validation {
    condition     = trimspace(var.platform_group_id) != ""
    error_message = "platform_group_id must not be empty."
  }
}

variable "readonly_group_id" {
  description = "Identity Store group ID for read-only engineering access."
  type        = string
  validation {
    condition     = trimspace(var.readonly_group_id) != ""
    error_message = "readonly_group_id must not be empty."
  }
}
