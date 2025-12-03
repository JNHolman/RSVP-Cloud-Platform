#########################################
# AI Log Summarizer Lambda
#########################################

resource "aws_iam_role" "ai_lambda_role" {
  name = "${var.project_name}-${var.environment}-ai-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect    = "Allow",
      Principal = { Service = "lambda.amazonaws.com" },
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "ai_lambda_policy" {
  name = "${var.project_name}-${var.environment}-ai-lambda-policy"
  role = aws_iam_role.ai_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = ["logs:FilterLogEvents"],
        Resource = "*"
      },
      {
        Effect   = "Allow",
        Action   = ["s3:PutObject"],
        Resource = "${aws_s3_bucket.ai_logs_bucket.arn}/*"
      },
      {
        Effect   = "Allow",
        Action   = ["dynamodb:PutItem"],
        Resource = aws_dynamodb_table.ai_logs.arn
      }
    ]
  })
}

#########################################
# S3 Bucket for summaries
#########################################

resource "aws_s3_bucket" "ai_logs_bucket" {
  bucket        = "${var.project_name}-${var.environment}-ai-logs"
  force_destroy = true
}

#########################################
# DynamoDB for history
#########################################

resource "aws_dynamodb_table" "ai_logs" {
  name         = "${var.project_name}-${var.environment}-ai-log-history"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }
}

#########################################
# Lambda Function
#########################################

resource "aws_lambda_function" "ai_log_summarizer" {
  function_name = "${var.project_name}-${var.environment}-ai-summarizer"
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.9"
  role          = aws_iam_role.ai_lambda_role.arn
  timeout       = 30

  filename         = "${path.module}/ai_lambda_package.zip"
  source_code_hash = filebase64sha256("${path.module}/ai_lambda_package.zip")

  environment {
    variables = {
      OPENAI_API_KEY = var.openai_api_key
      BUCKET_NAME    = aws_s3_bucket.ai_logs_bucket.bucket
      TABLE_NAME     = aws_dynamodb_table.ai_logs.name
    }
  }
}

#########################################
# Schedule (once daily)
#########################################

resource "aws_cloudwatch_event_rule" "daily_ai_summary" {
  name                = "${var.project_name}-${var.environment}-ai-summary-schedule"
  description         = "Daily AI log summary"
  schedule_expression = "rate(24 hours)"
}

resource "aws_cloudwatch_event_target" "ai_summary_target" {
  rule      = aws_cloudwatch_event_rule.daily_ai_summary.name
  target_id = "lambda"
  arn       = aws_lambda_function.ai_log_summarizer.arn
}

resource "aws_lambda_permission" "allow_events" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ai_log_summarizer.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_ai_summary.arn
}
