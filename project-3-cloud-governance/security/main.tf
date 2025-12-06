locals {
  alert_topic_name = "${var.project_name}-security-alerts"
}

resource "aws_sns_topic" "security_alerts" {
  name = local.alert_topic_name

  tags = merge(
    var.tags,
    {
      "Component" = "security"
    }
  )
}

resource "aws_sns_topic_subscription" "security_email" {
  topic_arn = aws_sns_topic.security_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# Placeholder for AI incident response Lambda + cost lambda.
# We'll fill these in next pass, wiring them to GuardDuty + Cost Explorer.

output "security_alert_topic_arn" {
  description = "SNS topic ARN for security / AI incident alerts"
  value       = aws_sns_topic.security_alerts.arn
}

output "ai_incidents_table_name" {
  description = "DynamoDB table name for AI incident summaries"
  value       = aws_dynamodb_table.ai_incidents.name
}

output "ai_cost_summaries_table_name" {
  description = "DynamoDB table name for AI cost summaries"
  value       = aws_dynamodb_table.ai_cost_summaries.name
}
