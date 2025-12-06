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
  name               = "${var.project_name}-dashboard-api-role"
  assume_role_policy = data.aws_iam_policy_document.dashboard_api_assume.json

  tags = merge(
    var.tags,
    {
      "Component" = "workload"
      "Service"   = "DashboardAPI"
    }
  )
}

# Basic logging
resource "aws_iam_role_policy_attachment" "dashboard_api_logs" {
  role       = aws_iam_role.dashboard_api_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Access to DynamoDB tables
data "aws_iam_policy_document" "dashboard_api_inline" {
  statement {
    effect = "Allow"
    actions = [
      "dynamodb:Query",
      "dynamodb:Scan",
      "dynamodb:GetItem"
    ]
    resources = [
      "arn:aws:dynamodb:${var.aws_region}:*:table/${var.ai_incidents_table_name}",
      "arn:aws:dynamodb:${var.aws_region}:*:table/${var.ai_cost_summaries_table_name}"
    ]
  }
}

resource "aws_iam_role_policy" "dashboard_api_inline" {
  name   = "${var.project_name}-dashboard-api-inline"
  role   = aws_iam_role.dashboard_api_role.id
  policy = data.aws_iam_policy_document.dashboard_api_inline.json
}
