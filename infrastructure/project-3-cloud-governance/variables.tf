variable "aws_region" {
  description = "AWS region to deploy governance stack"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Name prefix for all resources"
  type        = string
  default     = "rsvp-cloud-governance"
}

variable "alert_email" {
  description = "Email address for security and cost alerts"
  type        = string
}

variable "openai_api_key" {
  description = "OpenAI API key for AI incident & cost analysis"
  type        = string
  sensitive   = true
}

# For now these are logical names used in tags and resource naming.
# In a real multi-account setup, you’d map these to real account IDs.
variable "account_labels" {
  description = "Logical labels to simulate multi-account roles"
  type = object({
    management = string
    security   = string
    logging    = string
    workload   = string
  })
  default = {
    management = "mgmt"
    security   = "sec"
    logging    = "log"
    workload   = "workload"
  }
}
