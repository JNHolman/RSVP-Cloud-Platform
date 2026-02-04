# Package the cost Lambda
data "archive_file" "ai_cost_lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/ai_cost_lambda.py"
  output_path = "${path.module}/ai_cost_lambda.zip"
}

# Cost analysis Lambda function
resource "aws_lambda_function" "ai_cost" {
  function_name = "${var.project_name}-ai-cost-analyzer"
  role          = aws_iam_role.ai_cost_lambda_role.arn
  handler       = "ai_cost_lambda.handler"
  runtime       = "python3.10"

  filename         = data.archive_file.ai_cost_lambda_zip.output_path
  source_code_hash = data.archive_file.ai_cost_lambda_zip.output_base64sha256

  timeout     = 60
  memory_size = 256

  environment {
    variables = {
      OPENAI_API_KEY = var.openai_api_key
      COST_TABLE     = aws_dynamodb_table.ai_cost_summaries.name
      PROJECT_NAME   = var.project_name
    }
  }

  tags = merge(
    var.tags,
    {
      "Component" = "security"
      "Service"   = "AI-Cost-Lambda"
    }
  )
}

# EventBridge rule - trigger weekly (or can invoke manually)
resource "aws_cloudwatch_event_rule" "weekly_cost_analysis" {
  name                = "${var.project_name}-weekly-cost-analysis"
  description         = "Trigger AI cost analysis weekly"
  schedule_expression = "rate(7 days)"
}

resource "aws_cloudwatch_event_target" "cost_lambda_target" {
  rule      = aws_cloudwatch_event_rule.weekly_cost_analysis.name
  target_id = "ai-cost-lambda"
  arn       = aws_lambda_function.ai_cost.arn
}

resource "aws_lambda_permission" "allow_eventbridge_cost" {
  statement_id  = "AllowExecutionFromEventBridgeCost"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ai_cost.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.weekly_cost_analysis.arn
}
