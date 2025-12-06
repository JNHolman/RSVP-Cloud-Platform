variable "aws_region" {
  type = string
}

variable "project_name" {
  type = string
}

variable "tags" {
  type = map(string)
}

variable "security_alert_topic_arn" {
  type = string
}

variable "ai_incidents_table_name" {
  type        = string
  description = "DynamoDB table with AI incident summaries"
}

variable "ai_cost_summaries_table_name" {
  type        = string
  description = "DynamoDB table with AI cost summaries"
}
