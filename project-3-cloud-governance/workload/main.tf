resource "aws_cloudwatch_log_group" "api_access" {
  name              = "/aws/apigateway/${var.project_name}-${var.environment}-dashboard"
  retention_in_days = 90
  kms_key_id        = aws_kms_key.observability.arn

  tags = merge(var.tags, {
    Component = "workload"
    Service   = "DashboardAPI"
  })
}
