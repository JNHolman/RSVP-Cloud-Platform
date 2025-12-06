# In the full version, this module will:
# - Define EventBridge rules (e.g. forward specific events to Security)
# - Define IAM roles that Security account can assume
# - Define CloudWatch alarms for workload metrics

resource "aws_cloudwatch_log_group" "workload_app_logs" {
  name              = "/${var.project_name}/workload/app"
  retention_in_days = 30

  tags = merge(
    var.tags,
    {
      "Component" = "workload"
    }
  )
}
