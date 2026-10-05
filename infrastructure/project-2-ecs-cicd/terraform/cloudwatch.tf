resource "aws_cloudwatch_log_group" "ecs_app" {
  name              = "/ecs/${local.name_prefix}-app"
  retention_in_days = var.log_retention_days
  kms_key_id        = aws_kms_key.observability.arn

  tags = {
    Name        = "${local.name_prefix}-log-group"
    Project     = var.project_name
    Environment = var.environment
  }
}
