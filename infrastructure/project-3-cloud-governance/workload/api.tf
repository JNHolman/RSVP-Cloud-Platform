data "archive_file" "dashboard_api_zip" {
  type        = "zip"
  source_file = "${path.module}/dashboard_api.py"
  output_path = "${path.module}/dashboard_api.zip"
}

resource "aws_lambda_function" "dashboard_api" {
  #checkov:skip=CKV_AWS_116:API Gateway invokes this Lambda synchronously; async Lambda DLQ semantics do not apply to request/response failures.
  #checkov:skip=CKV_AWS_117:This API Lambda only calls STS and DynamoDB through public AWS service endpoints; VPC attachment would add NAT dependency without a private resource boundary.
  function_name = "${var.project_name}-${var.environment}-dashboard-api"
  role          = aws_iam_role.dashboard_api_role.arn
  handler       = "dashboard_api.handler"
  runtime       = "python3.12"

  filename         = data.archive_file.dashboard_api_zip.output_path
  source_code_hash = data.archive_file.dashboard_api_zip.output_base64sha256

  timeout                        = 10
  memory_size                    = 256
  reserved_concurrent_executions = 10
  kms_key_arn                    = aws_kms_key.observability.arn

  tracing_config {
    mode = "Active"
  }

  depends_on = [
    aws_cloudwatch_log_group.dashboard_lambda,
    aws_iam_role_policy_attachment.dashboard_api_logs,
    aws_iam_role_policy_attachment.dashboard_xray,
    aws_iam_role_policy.dashboard_api_inline,
  ]

  environment {
    variables = {
      INCIDENTS_TABLE      = var.ai_incidents_table_name
      COST_SUMMARIES_TABLE = var.ai_cost_summaries_table_name
      APP_REGION           = var.aws_region
      MAX_ITEMS            = "50"
      ALLOWED_ORIGINS      = var.dashboard_allowed_origin
      SECURITY_READ_ROLE_ARN = var.security_data_read_role_arn
      FINOPS_READ_ROLE_ARN   = var.finops_data_read_role_arn
    }
  }

  tags = merge(var.tags, {
    Component = "workload"
    Service   = "DashboardAPI"
  })
}

resource "aws_cognito_user_pool" "dashboard" {
  name                = "${var.project_name}-${var.environment}-dashboard-users"
  deletion_protection = var.environment == "prod" ? "ACTIVE" : "INACTIVE"

  mfa_configuration = "ON"

  # This dashboard is an internal operations surface. Users must be provisioned
  # administratively; unauthenticated public SignUp is intentionally disabled.
  admin_create_user_config {
    allow_admin_create_user_only = true
  }

  software_token_mfa_configuration {
    enabled = true
  }

  password_policy {
    minimum_length                   = 14
    require_lowercase                = true
    require_numbers                  = true
    require_symbols                  = true
    require_uppercase                = true
    temporary_password_validity_days = 1
  }

  tags = var.tags
}

resource "aws_cognito_user_pool_client" "dashboard" {
  name         = "${var.project_name}-${var.environment}-dashboard-client"
  user_pool_id = aws_cognito_user_pool.dashboard.id

  generate_secret = false

  explicit_auth_flows = [
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_SRP_AUTH"
  ]

  prevent_user_existence_errors = "ENABLED"

  access_token_validity  = 60
  id_token_validity      = 60
  refresh_token_validity = 7

  token_validity_units {
    access_token  = "minutes"
    id_token      = "minutes"
    refresh_token = "days"
  }
}

resource "aws_api_gateway_rest_api" "dashboard" {
  name        = "${var.project_name}-${var.environment}-dashboard-api"
  description = "Authenticated RSVP governance dashboard API"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  minimum_compression_size = 1024

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_authorizer" "cognito" {
  name          = "dashboard-cognito"
  rest_api_id   = aws_api_gateway_rest_api.dashboard.id
  type          = "COGNITO_USER_POOLS"
  provider_arns = [aws_cognito_user_pool.dashboard.arn]
}

locals {
  protected_resources = {
    incidents    = "incidents"
    cost_summary = "cost-summary"
  }
}

resource "aws_api_gateway_resource" "protected" {
  for_each = local.protected_resources

  rest_api_id = aws_api_gateway_rest_api.dashboard.id
  parent_id   = aws_api_gateway_rest_api.dashboard.root_resource_id
  path_part   = each.value
}

resource "aws_api_gateway_method" "get" {
  for_each = local.protected_resources

  rest_api_id   = aws_api_gateway_rest_api.dashboard.id
  resource_id   = aws_api_gateway_resource.protected[each.key].id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id
}

resource "aws_api_gateway_integration" "lambda" {
  for_each = local.protected_resources

  rest_api_id             = aws_api_gateway_rest_api.dashboard.id
  resource_id             = aws_api_gateway_resource.protected[each.key].id
  http_method             = aws_api_gateway_method.get[each.key].http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.dashboard_api.invoke_arn
}

resource "aws_api_gateway_method" "options" {
  for_each = local.protected_resources

  rest_api_id   = aws_api_gateway_rest_api.dashboard.id
  resource_id   = aws_api_gateway_resource.protected[each.key].id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "options" {
  for_each = local.protected_resources

  rest_api_id = aws_api_gateway_rest_api.dashboard.id
  resource_id = aws_api_gateway_resource.protected[each.key].id
  http_method = aws_api_gateway_method.options[each.key].http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 204}"
  }
}

resource "aws_api_gateway_method_response" "options" {
  for_each = local.protected_resources

  rest_api_id = aws_api_gateway_rest_api.dashboard.id
  resource_id = aws_api_gateway_resource.protected[each.key].id
  http_method = aws_api_gateway_method.options[each.key].http_method
  status_code = "204"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "options" {
  for_each = local.protected_resources

  rest_api_id = aws_api_gateway_rest_api.dashboard.id
  resource_id = aws_api_gateway_resource.protected[each.key].id
  http_method = aws_api_gateway_method.options[each.key].http_method
  status_code = aws_api_gateway_method_response.options[each.key].status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Authorization,Content-Type'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'${var.dashboard_allowed_origin}'"
  }
}

resource "aws_lambda_permission" "allow_apigw_invoke" {
  statement_id  = "AllowDashboardApiGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.dashboard_api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.dashboard.execution_arn}/*/GET/*"
}

resource "aws_api_gateway_deployment" "dashboard" {
  rest_api_id = aws_api_gateway_rest_api.dashboard.id

  triggers = {
    redeployment = sha1(jsonencode({
      resources                     = aws_api_gateway_resource.protected
      get_methods                   = aws_api_gateway_method.get
      get_integrations              = aws_api_gateway_integration.lambda
      options_methods               = aws_api_gateway_method.options
      options_integrations          = aws_api_gateway_integration.options
      options_method_responses      = aws_api_gateway_method_response.options
      options_integration_responses = aws_api_gateway_integration_response.options
      authorizer                    = aws_api_gateway_authorizer.cognito
      default_4xx                   = aws_api_gateway_gateway_response.default_4xx
      default_5xx                   = aws_api_gateway_gateway_response.default_5xx
      cors                          = var.dashboard_allowed_origin
    }))
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    aws_api_gateway_integration.lambda,
    aws_api_gateway_integration_response.options
  ]
}

resource "aws_api_gateway_stage" "dashboard" {
  deployment_id = aws_api_gateway_deployment.dashboard.id
  rest_api_id   = aws_api_gateway_rest_api.dashboard.id
  stage_name    = var.environment

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_access.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      sourceIp       = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      resourcePath   = "$context.resourcePath"
      status         = "$context.status"
      responseLength = "$context.responseLength"
      integrationErr = "$context.integrationErrorMessage"
    })
  }

  xray_tracing_enabled = true

  tags = var.tags
}

resource "aws_api_gateway_method_settings" "all" {
  depends_on = [aws_api_gateway_account.this]
  rest_api_id = aws_api_gateway_rest_api.dashboard.id
  stage_name  = aws_api_gateway_stage.dashboard.stage_name
  method_path = "*/*"

  settings {
    metrics_enabled        = true
    logging_level          = "ERROR"
    data_trace_enabled     = false
    throttling_rate_limit  = var.api_throttle_rate_limit
    throttling_burst_limit = var.api_throttle_burst_limit
  }
}

output "dashboard_api_url" {
  value = "${aws_api_gateway_stage.dashboard.invoke_url}"
}

output "dashboard_user_pool_id" {
  value = aws_cognito_user_pool.dashboard.id
}

output "dashboard_user_pool_client_id" {
  value = aws_cognito_user_pool_client.dashboard.id
}

resource "aws_api_gateway_gateway_response" "default_4xx" {
  rest_api_id   = aws_api_gateway_rest_api.dashboard.id
  response_type = "DEFAULT_4XX"

  response_parameters = {
    "gatewayresponse.header.Access-Control-Allow-Origin" = "'${var.dashboard_allowed_origin}'"
    "gatewayresponse.header.Cache-Control"               = "'no-store'"
    "gatewayresponse.header.X-Content-Type-Options"      = "'nosniff'"
    "gatewayresponse.header.X-Frame-Options"             = "'DENY'"
  }
}

resource "aws_api_gateway_gateway_response" "default_5xx" {
  rest_api_id   = aws_api_gateway_rest_api.dashboard.id
  response_type = "DEFAULT_5XX"

  response_parameters = {
    "gatewayresponse.header.Access-Control-Allow-Origin" = "'${var.dashboard_allowed_origin}'"
    "gatewayresponse.header.Cache-Control"               = "'no-store'"
    "gatewayresponse.header.X-Content-Type-Options"      = "'nosniff'"
    "gatewayresponse.header.X-Frame-Options"             = "'DENY'"
  }
}
