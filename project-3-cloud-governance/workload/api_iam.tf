data "aws_iam_policy_document" "dashboard_api_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "dashboard_api_role" {
  name               = "${var.project_name}-${var.environment}-dashboard-api-role"
  assume_role_policy = data.aws_iam_policy_document.dashboard_api_assume.json
  tags               = var.tags
}

resource "aws_iam_role_policy_attachment" "dashboard_api_logs" {
  role       = aws_iam_role.dashboard_api_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "dashboard_api_inline" {
  statement {
    sid       = "AssumeReadOnlyDataRoles"
    effect    = "Allow"
    actions   = ["sts:AssumeRole"]
    resources = [var.security_data_read_role_arn, var.finops_data_read_role_arn]
  }
}

resource "aws_iam_role_policy_attachment" "dashboard_xray" {
  role       = aws_iam_role.dashboard_api_role.name
  policy_arn = "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess"
}

resource "aws_iam_role_policy" "dashboard_api_inline" {
  name   = "${var.project_name}-${var.environment}-dashboard-api"
  role   = aws_iam_role.dashboard_api_role.id
  policy = data.aws_iam_policy_document.dashboard_api_inline.json
}

data "aws_iam_policy_document" "apigw_logs_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["apigateway.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "apigw_logs" {
  name               = "${var.project_name}-${var.environment}-apigw-logs"
  assume_role_policy = data.aws_iam_policy_document.apigw_logs_assume.json
  tags               = var.tags
}

resource "aws_iam_role_policy_attachment" "apigw_logs" {
  role       = aws_iam_role.apigw_logs.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"
}

resource "aws_api_gateway_account" "this" {
  cloudwatch_role_arn = aws_iam_role.apigw_logs.arn

  depends_on = [aws_iam_role_policy_attachment.apigw_logs]
}
