variable "aws_region" {
  description = "Home AWS Region for organization-level integrations."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Lowercase resource prefix. Length is bounded so generated organization policy and related resource names remain portable across stacks."
  type        = string
  default     = "rsvp-enterprise"

  validation {
    condition     = can(regex("^[a-z0-9]([a-z0-9-]{0,30}[a-z0-9])?$", var.project_name))
    error_message = "project_name must be 1-32 characters, use lowercase letters/numbers/hyphens only, and start/end with a letter or number."
  }
}

variable "owner" {
  description = "Owner tag applied to organization resources where supported."
  type        = string
  default     = "Josh Holman"
}

variable "create_member_accounts" {
  description = "Create and place member accounts in the Terraform-managed OUs. Leave false to reference pre-existing account IDs; this stack does not move existing accounts between OUs."
  type        = bool
  default     = false
}

variable "member_account_emails" {
  description = "Unique root emails used only when create_member_accounts=true."
  type = object({
    security        = string
    log_archive     = string
    shared_services = string
    nonprod         = string
    prod            = string
  })
  default = {
    security        = ""
    log_archive     = ""
    shared_services = ""
    nonprod         = ""
    prod            = ""
  }

  validation {
    condition = alltrue([
      for email in values(var.member_account_emails) : email == "" || can(regex("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", email))
    ])
    error_message = "Each non-empty member account email must be valid."
  }
}

variable "existing_account_ids" {
  description = "Existing 12-digit account IDs referenced when create_member_accounts=false. Supplying IDs does not adopt or move those accounts into Terraform-managed OUs."
  type = object({
    security        = string
    log_archive     = string
    shared_services = string
    nonprod         = string
    prod            = string
  })
  default = {
    security        = ""
    log_archive     = ""
    shared_services = ""
    nonprod         = ""
    prod            = ""
  }

  validation {
    condition = alltrue([
      for id in values(var.existing_account_ids) : id == "" || can(regex("^[0-9]{12}$", id))
    ])
    error_message = "Each non-empty existing account ID must be a 12-digit AWS account ID."
  }
}


variable "configure_delegated_admins" {
  description = "Register delegated administrators after valid member account IDs exist."
  type        = bool
  default     = false
}

variable "stacksets_trusted_access_activated" {
  description = "Set true only after CloudFormation StackSets trusted access has been activated from the management account using CloudFormation ActivateOrganizationsAccess (or the console). Terraform then preserves the service-access principal and may register the Shared Services delegated administrator."
  type        = bool
  default     = false
}

variable "account_access_role_name" {
  description = "Bootstrap role created in newly provisioned member accounts."
  type        = string
  default     = "OrganizationAccountAccessRole"
}

variable "protected_admin_role_patterns" {
  description = "Explicit account-scoped IAM role ARNs exempted from security-control SCP denies. Empty by default; wildcard account IDs are intentionally rejected."
  type        = list(string)
  default     = []

  validation {
    condition = alltrue([
      for arn in var.protected_admin_role_patterns :
      can(regex("^arn:(aws|aws-us-gov|aws-cn):iam::[0-9]{12}:role/.+$", arn)) && !strcontains(arn, "*")
    ])
    error_message = "Each protected admin principal must be an explicit IAM role ARN with a 12-digit account ID; wildcards are not allowed."
  }
}
