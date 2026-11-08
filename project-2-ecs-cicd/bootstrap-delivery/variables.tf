variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project_name" {
  type    = string
  default = "rsvp-project2"

  validation {
    condition     = can(regex("^[a-z0-9]([a-z0-9-]{0,20}[a-z0-9])?$", var.project_name))
    error_message = "project_name must be 1-22 characters, use lowercase letters/numbers/hyphens only, and start/end with a letter or number."
  }
}

variable "github_repository" {
  description = "GitHub owner/repository allowed to assume deployment roles"
  type        = string
  default     = "JNHolman/RSVP-Cloud-Platform"
}

variable "environments" {
  description = "Application environments bootstrapped in this AWS account"
  type        = set(string)
  default     = ["dev", "stage", "prod"]

  validation {
    condition     = alltrue([for env in var.environments : contains(["dev", "stage", "prod"], env)])
    error_message = "environments may contain only dev, stage, and prod."
  }
}
