output "alb_dns_name" {
  description = "Public DNS name of the Application Load Balancer"
  value       = aws_lb.this.dns_name
}

output "application_url" {
  description = "Production HTTPS URL"
  value       = "https://${var.domain_name}/"
}

output "operations_dashboard_name" {
  description = "CloudWatch operations dashboard"
  value       = aws_cloudwatch_dashboard.operations.dashboard_name
}

output "operations_topic_arn" {
  description = "SNS topic for ECS operational alerts"
  value       = aws_sns_topic.operations.arn
}
