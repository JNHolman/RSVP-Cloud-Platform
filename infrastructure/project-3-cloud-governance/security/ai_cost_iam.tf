# IAM role for cost analysis Lambda
resource "aws_iam_role" "ai_cost_lambda_role" {
  name = "${var.project_name}-ai-cost-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })

  tags = var.tags
}

# Inline policy for cost Lambda
resource "aws_iam_role_policy" "ai_cost_inline" {
  name = "ai-cost-lambda-permissions"
  role = aws_iam_role.ai_cost_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:UpdateItem"
        ]
        Resource = aws_dynamodb_table.ai_cost_summaries.arn
      },
      {
        Effect = "Allow"
        Action = [
          "ce:GetCostAndUsage",
          "ce:GetCostForecast"
        ]
        Resource = "*"
      }
    ]
  })
}

# CloudWatch Logs permissions
resource "aws_iam_role_policy_attachment" "ai_cost_logs" {
  role       = aws_iam_role.ai_cost_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
