variable "aws_region" {
  type = string
}

variable "project_name" {
  type = string
}

variable "alert_email" {
  type = string
}

variable "openai_api_key" {
  type      = string
  sensitive = true
}

variable "tags" {
  type = map(string)
}

variable "logging_bucket_arn" {
  description = "Central logging bucket ARN"
  type        = string
}
