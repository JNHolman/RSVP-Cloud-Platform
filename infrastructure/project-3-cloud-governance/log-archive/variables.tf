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

variable "organization_id" {
  description = "AWS Organizations ID, for example o-abc123xyz."
  type        = string

  validation {
    condition     = can(regex("^o-[a-z0-9]{10,32}$", var.organization_id))
    error_message = "organization_id must be a valid AWS Organizations ID."
  }
}

variable "management_account_id" {
  type = string

  validation {
    condition     = can(regex("^[0-9]{12}$", var.management_account_id))
    error_message = "management_account_id must be a 12-digit AWS account ID."
  }
}

variable "organization_trail_name" {
  type    = string
  default = "rsvp-enterprise-organization-trail"
}
