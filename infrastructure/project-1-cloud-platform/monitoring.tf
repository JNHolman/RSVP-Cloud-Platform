##############################################
# SNS alerting
##############################################
resource "aws_sns_topic" "alerts" {
  name              = "${local.name_prefix}-alerts"
  kms_master_key_id = aws_kms_key.observability.arn
}

resource "aws_sns_topic_subscription" "alerts_email" {
  count     = var.alert_email == "" ? 0 : 1
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

##############################################
# Application / infrastructure alarms
##############################################
resource "aws_cloudwatch_metric_alarm" "alb_5xx_high" {
  alarm_name          = "${local.name_prefix}-alb-5xx-high"
  alarm_description   = "ALB is returning elevated 5XX responses"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  datapoints_to_alarm  = 2
  metric_name          = "HTTPCode_ELB_5XX_Count"
  namespace            = "AWS/ApplicationELB"
  period               = 60
  statistic            = "Sum"
  threshold            = var.alarm_alb_5xx_threshold
  treat_missing_data   = "notBreaching"
  dimensions = { LoadBalancer = aws_lb.app_alb.arn_suffix }
  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "target_5xx_high" {
  alarm_name          = "${local.name_prefix}-target-5xx-high"
  alarm_description   = "Application targets are returning elevated 5XX responses"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  datapoints_to_alarm  = 2
  metric_name          = "HTTPCode_Target_5XX_Count"
  namespace            = "AWS/ApplicationELB"
  period               = 60
  statistic            = "Sum"
  threshold            = var.alarm_alb_5xx_threshold
  treat_missing_data   = "notBreaching"
  dimensions = {
    LoadBalancer = aws_lb.app_alb.arn_suffix
    TargetGroup  = aws_lb_target_group.app_tg.arn_suffix
  }
  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "unhealthy_targets" {
  alarm_name          = "${local.name_prefix}-unhealthy-targets"
  alarm_description   = "One or more ALB targets are unhealthy"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  datapoints_to_alarm  = 2
  metric_name          = "UnHealthyHostCount"
  namespace            = "AWS/ApplicationELB"
  period               = 60
  statistic            = "Maximum"
  threshold            = 0
  treat_missing_data   = "breaching"
  dimensions = {
    LoadBalancer = aws_lb.app_alb.arn_suffix
    TargetGroup  = aws_lb_target_group.app_tg.arn_suffix
  }
  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "asg_cpu_high" {
  alarm_name          = "${local.name_prefix}-asg-cpu-high"
  alarm_description   = "App ASG average CPU is elevated"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  datapoints_to_alarm  = 2
  metric_name          = "CPUUtilization"
  namespace            = "AWS/EC2"
  period               = 60
  statistic            = "Average"
  threshold            = var.alarm_asg_cpu_threshold
  treat_missing_data   = "notBreaching"
  dimensions = { AutoScalingGroupName = aws_autoscaling_group.app_asg.name }
  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "rds_cpu_high" {
  alarm_name          = "${local.name_prefix}-rds-cpu-high"
  alarm_description   = "RDS CPU is above the production threshold"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 5
  datapoints_to_alarm  = 3
  metric_name          = "CPUUtilization"
  namespace            = "AWS/RDS"
  period               = 60
  statistic            = "Average"
  threshold            = var.alarm_rds_cpu_threshold
  treat_missing_data   = "notBreaching"
  dimensions = { DBInstanceIdentifier = aws_db_instance.app_db.identifier }
  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "rds_free_storage_low" {
  alarm_name          = "${local.name_prefix}-rds-free-storage-low"
  alarm_description   = "RDS free storage is below the minimum operational buffer"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 3
  datapoints_to_alarm  = 2
  metric_name          = "FreeStorageSpace"
  namespace            = "AWS/RDS"
  period               = 300
  statistic            = "Average"
  threshold            = var.alarm_rds_free_storage_bytes
  treat_missing_data   = "breaching"
  dimensions = { DBInstanceIdentifier = aws_db_instance.app_db.identifier }
  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "ai_lambda_errors" {
  count               = var.enable_lambda_error_alarm ? 1 : 0
  alarm_name          = "${local.name_prefix}-ai-lambda-errors"
  alarm_description   = "AI log summarizer Lambda is erroring"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name          = "Errors"
  namespace            = "AWS/Lambda"
  period               = 60
  statistic            = "Sum"
  threshold            = 1
  treat_missing_data   = "notBreaching"
  dimensions = { FunctionName = aws_lambda_function.ai_log_summarizer.function_name }
  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]
}

##############################################
# Operator dashboard
##############################################
resource "aws_cloudwatch_dashboard" "operations" {
  dashboard_name = "${local.name_prefix}-operations"
  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric", x = 0, y = 0, width = 12, height = 6,
        properties = {
          title = "ALB requests, latency and 5XX"
          region = var.aws_region
          period = 60
          metrics = [
            ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", aws_lb.app_alb.arn_suffix, { stat = "Sum" }],
            [".", "TargetResponseTime", ".", ".", { stat = "p95", yAxis = "right" }],
            [".", "HTTPCode_ELB_5XX_Count", ".", ".", { stat = "Sum" }]
          ]
        }
      },
      {
        type = "metric", x = 12, y = 0, width = 12, height = 6,
        properties = {
          title = "Target health"
          region = var.aws_region
          period = 60
          metrics = [
            ["AWS/ApplicationELB", "HealthyHostCount", "TargetGroup", aws_lb_target_group.app_tg.arn_suffix, "LoadBalancer", aws_lb.app_alb.arn_suffix, { stat = "Minimum" }],
            [".", "UnHealthyHostCount", ".", ".", ".", ".", { stat = "Maximum" }]
          ]
        }
      },
      {
        type = "metric", x = 0, y = 6, width = 12, height = 6,
        properties = {
          title = "EC2 ASG CPU"
          region = var.aws_region
          period = 60
          metrics = [["AWS/EC2", "CPUUtilization", "AutoScalingGroupName", aws_autoscaling_group.app_asg.name, { stat = "Average" }]]
        }
      },
      {
        type = "metric", x = 12, y = 6, width = 12, height = 6,
        properties = {
          title = "RDS health"
          region = var.aws_region
          period = 60
          metrics = [
            ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", aws_db_instance.app_db.identifier, { stat = "Average" }],
            [".", "DatabaseConnections", ".", ".", { stat = "Average" }],
            [".", "FreeStorageSpace", ".", ".", { stat = "Average", yAxis = "right" }]
          ]
        }
      }
    ]
  })
}
