##############################################
#  CloudWatch Monitoring & Alarms
##############################################

# SNS topic for alerts
resource "aws_sns_topic" "alerts" {
  name = "${var.project_name}-${var.environment}-alerts"

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

# (Optional) email subscription – set your email in AWS console manually
# so we don’t hard-code it here.

##############################################
#  ALB 5xx error alarm
##############################################

resource "aws_cloudwatch_metric_alarm" "alb_5xx" {
  alarm_name          = "${var.project_name}-${var.environment}-alb-5xx-errors"
  alarm_description   = "High rate of 5xx errors on ALB"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  period              = 300
  statistic           = "Sum"
  threshold           = 10

  metric_name = "HTTPCode_ELB_5XX_Count"
  namespace   = "AWS/ApplicationELB"

  dimensions = {
    LoadBalancer = aws_lb.app_alb.arn_suffix
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]

  treat_missing_data = "notBreaching"
}

##############################################
#  EC2 CPU alarm
##############################################

resource "aws_cloudwatch_metric_alarm" "ec2_cpu_high" {
  alarm_name          = "${var.project_name}-${var.environment}-ec2-cpu-high"
  alarm_description   = "High CPU on app EC2 instances"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  period              = 300
  statistic           = "Average"
  threshold           = 80

  metric_name = "CPUUtilization"
  namespace   = "AWS/EC2"

  # Attach the alarm to the first EC2 instance
  dimensions = {
    InstanceId = aws_instance.app[0].id
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]

  treat_missing_data = "notBreaching"
}

##############################################
#  Simple CloudWatch Dashboard
##############################################

resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project_name}-${var.environment}-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title = "ALB 5xx Errors"
          metrics = [
            ["AWS/ApplicationELB", "HTTPCode_ELB_5XX_Count", "LoadBalancer", aws_lb.app_alb.arn_suffix]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title = "App EC2 CPU"
          metrics = [
            ["AWS/EC2", "CPUUtilization", "InstanceId", aws_instance.app[0].id]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
        }
      }
    ]
  })
}
