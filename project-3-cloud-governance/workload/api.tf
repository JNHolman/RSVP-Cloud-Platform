resource "aws_lambda_function" "dashboard_api" {
  function_name = "${var.project_name}-dashboard-api"
  role          = aws_iam_role.dashboard_api_role.arn
  handler       = "dashboard_api.handler"
  runtime       = "python3.10"

  filename         = "${path.module}/dashboard_api.zip"
  source_code_hash = filebase64sha256("${path.module}/dashboard_api.zip")

  timeout     = 30
  memory_size = 256

  environment {
    variables = {
      INCIDENTS_TABLE      = var.ai_incidents_table_name
      COST_SUMMARIES_TABLE = var.ai_cost_summaries_table_name
      APP_REGION           = var.aws_region
    }
  }

  tags = merge(
    var.tags,
    {
      "Component" = "workload"
      "Service"   = "DashboardAPI"
    }
  )
}

# HTTP API (API Gateway v2)
resource "aws_apigatewayv2_api" "dashboard_api" {
  name          = "${var.project_name}-http-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "OPTIONS"]
    allow_headers = ["*"]
  }
}

resource "aws_apigatewayv2_integration" "dashboard_api_integration" {
  api_id           = aws_apigatewayv2_api.dashboard_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.dashboard_api.arn
  integration_method = "POST"
  payload_format_version = "2.0"
}

# Route for /incidents
resource "aws_apigatewayv2_route" "incidents_route" {
  api_id    = aws_apigatewayv2_api.dashboard_api.id
  route_key = "GET /incidents"
  target    = "integrations/${aws_apigatewayv2_integration.dashboard_api_integration.id}"
}

# Route for /cost-summary
resource "aws_apigatewayv2_route" "cost_summary_route" {
  api_id    = aws_apigatewayv2_api.dashboard_api.id
  route_key = "GET /cost-summary"
  target    = "integrations/${aws_apigatewayv2_integration.dashboard_api_integration.id}"
}

# Default stage with auto-deploy
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.dashboard_api.id
  name        = "$default"
  auto_deploy = true
}

# Allow API Gateway to invoke the Lambda
resource "aws_lambda_permission" "allow_apigw_invoke" {
  statement_id  = "AllowAPIGatewayInvokeDashboardAPI"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.dashboard_api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.dashboard_api.execution_arn}/*/*"
}

output "dashboard_api_url" {
  description = "Base URL for the Dashboard HTTP API"
  value       = aws_apigatewayv2_api.dashboard_api.api_endpoint
}
