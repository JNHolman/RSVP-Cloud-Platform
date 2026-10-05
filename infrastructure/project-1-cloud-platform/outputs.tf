output "vpc_id" {
  description = "ID of the main VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "alb_dns_name" {
  description = "DNS name of the application load balancer"
  value       = aws_lb.app_alb.dns_name
}

output "application_url" {
  description = "Production HTTPS URL"
  value       = "https://${var.domain_name}/"
}

output "alb_health_url" {
  description = "HTTPS health endpoint"
  value       = "https://${var.domain_name}/health"
}

output "rds_endpoint" {
  description = "RDS endpoint"
  value       = aws_db_instance.app_db.endpoint
}

output "asg_name" {
  description = "Application Auto Scaling Group name"
  value       = aws_autoscaling_group.app_asg.name
}

output "alerts_topic_arn" {
  description = "SNS topic ARN for alerts"
  value       = aws_sns_topic.alerts.arn
}

output "ai_logs_bucket" {
  description = "S3 bucket for AI log summaries"
  value       = aws_s3_bucket.ai_logs.bucket
}

output "ai_logs_prefix" {
  description = "S3 prefix where summaries are stored"
  value       = "summaries/"
}

output "ai_log_summaries_table" {
  description = "DynamoDB table storing AI log summaries"
  value       = aws_dynamodb_table.ai_log_summaries.name
}

output "ai_lambda_function_name" {
  description = "AI log summarizer Lambda function name"
  value       = aws_lambda_function.ai_log_summarizer.function_name
}

output "app_log_group_name" {
  description = "CloudWatch log group intended for app logs"
  value       = aws_cloudwatch_log_group.app_logs.name
}

output "ai_lambda_log_group_name" {
  description = "CloudWatch log group for the AI summarizer Lambda"
  value       = "/aws/lambda/${aws_lambda_function.ai_log_summarizer.function_name}"
}

output "rds_master_secret_arn" {
  description = "Secrets Manager ARN containing the RDS-managed master credential"
  value       = aws_db_instance.app_db.master_user_secret[0].secret_arn
  sensitive   = true
}

output "rds_kms_key_arn" {
  description = "KMS key ARN protecting RDS storage, credentials, and Performance Insights"
  value       = aws_kms_key.rds.arn
}

output "operations_dashboard_name" {
  description = "CloudWatch operations dashboard"
  value       = aws_cloudwatch_dashboard.operations.dashboard_name
}

output "backup_vault_name" {
  description = "AWS Backup vault used for independent RDS recovery points"
  value       = aws_backup_vault.production.name
}
