variable "aws_region" {
  type        = string
  description = "AWS region"
}

variable "project_name" {
  type        = string
  description = "Project name prefix"
}

variable "account_labels" {
  description = "Logical names for simulated accounts"
  type = object({
    management = string
    security   = string
    logging    = string
    workload   = string
  })
}

variable "tags" {
  description = "Base tags to apply to resources"
  type        = map(string)
}
