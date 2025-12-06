data "aws_iam_policy_document" "ai_incident_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ai_incident_lambda_role" {
  name               = "${var.project_name}-ai-incident-role"
  assume_role_policy = data.aws_iam_policy_document.ai_incident_assume.json

  tags = merge(
    var.tags,
    {
      "Component" = "security"
      "Service"   = "AI-Incident-Lambda"
    }
  )
}

resource "aws_dynamodb_table" "ai_cost_summaries" {
  name         = "${var.project_name}-ai-cost-summaries"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "report_id"

  attribute {
    name = "report_id"
    type = "S"
  }

  tags = merge(
    var.tags,
    {
      "Component" = "security"
      "Service"   = "AI-Cost-Summaries"
    }
  )
}


# Basic logging
resource "aws_iam_role_policy_attachment" "ai_incident_logs" {
  role       = aws_iam_role.ai_incident_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Access to DynamoDB + SNS + GuardDuty (read)
data "aws_iam_policy_document" "ai_incident_inline" {
  statement {
    effect = "Allow"
    actions = [
      "dynamodb:PutItem"
    ]
    resources = [
      aws_dynamodb_table.ai_incidents.arn
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "sns:Publish"
    ]
    resources = [
      aws_sns_topic.security_alerts.arn
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "guardduty:GetFindings"
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "ai_incident_inline" {
  name   = "${var.project_name}-ai-incident-inline"
  role   = aws_iam_role.ai_incident_lambda_role.id
  policy = data.aws_iam_policy_document.ai_incident_inline.json
}
