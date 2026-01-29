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

# Added: direct URLs for verification/evidence
output "alb_http_url" {
  description = "HTTP URL for the ALB (landing page)"
  value       = "http://${aws_lb.app_alb.dns_name}/"
}

output "alb_health_url" {
  description = "HTTP health endpoint (target group health check)"
  value       = "http://${aws_lb.app_alb.dns_name}/health"
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

# Added: stable prefix for evidence scripts
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

# Added: log group names for evidence/verification
output "app_log_group_name" {
  description = "CloudWatch log group intended for app logs"
  value       = aws_cloudwatch_log_group.app_logs.name
}

output "ai_lambda_log_group_name" {
  description = "CloudWatch log group for the AI summarizer Lambda"
  value       = "/aws/lambda/${aws_lambda_function.ai_log_summarizer.function_name}"
}
