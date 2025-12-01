##############################################
#  AI Log Summarizer – Skeleton
##############################################

# CloudWatch log group where app / ALB logs could be sent
resource "aws_cloudwatch_log_group" "app_logs" {
  name              = "/aws/rsvp/${var.environment}/app"
  retention_in_days = 7

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

##############################################
#  SNS Topic for AI Summaries
##############################################

resource "aws_sns_topic" "ai_summaries" {
  name = "${var.project_name}-${var.environment}-ai-log-summaries"

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

##############################################
#  Lambda Function Placeholder (AI Summarizer)
##############################################

# NOTE:
# - In a real deployment, you’d package lambda_function.py as a ZIP
# - And configure environment variables for model + SNS topic
# - For now, we wire the infra side so you can explain the design.

resource "aws_lambda_function" "ai_log_summarizer" {
  function_name = "${var.project_name}-${var.environment}-ai-log-summarizer"
  role          = aws_iam_role.ai_logs_lambda_role.arn
  runtime       = "python3.9"
  handler       = "lambda_function.lambda_handler"

  # Placeholder – in a real setup you'd point to an S3 object or local file
  filename         = "lambda/ai-log-summarizer.zip"
  source_code_hash = filebase64sha256("lambda/ai-log-summarizer.zip")

  timeout = 60

  environment {
    variables = {
      LOG_GROUP_NAME = aws_cloudwatch_log_group.app_logs.name
      SNS_TOPIC_ARN  = aws_sns_topic.ai_summaries.arn
      AWS_REGION     = var.aws_region
      # MODEL_ID     = "bedrock-model-id-here"
    }
  }

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

##############################################
#  EventBridge Rule – Run Summarizer Periodically
##############################################

resource "aws_cloudwatch_event_rule" "ai_logs_schedule" {
  name                = "${var.project_name}-${var.environment}-ai-logs-schedule"
  description         = "Run AI log summarizer on a schedule"
  schedule_expression = "rate(1 day)"

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

resource "aws_cloudwatch_event_target" "ai_logs_target" {
  rule      = aws_cloudwatch_event_rule.ai_logs_schedule.name
  target_id = "ai-log-summarizer"
  arn       = aws_lambda_function.ai_log_summarizer.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ai_log_summarizer.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.ai_logs_schedule.arn
}
