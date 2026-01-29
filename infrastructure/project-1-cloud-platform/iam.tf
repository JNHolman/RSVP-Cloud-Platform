##############################################
#  IAM for EC2
##############################################

resource "aws_iam_role" "ec2_role" {
  name = "${local.name_prefix}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ec2_basic_ssm" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "ec2_instance_profile" {
  name = "${local.name_prefix}-ec2-instance-profile"
  role = aws_iam_role.ec2_role.name
}

# Allow EC2 instances to write to CloudWatch Logs (if/when you enable log shipping)
resource "aws_iam_role_policy_attachment" "ec2_cloudwatch_logs" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}

##############################################
#  IAM for AI Lambda
##############################################

resource "aws_iam_role" "ai_lambda_role" {
  name = "${local.name_prefix}-ai-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action = "sts:AssumeRole"
    }]
  })
}

# Basic execution (Lambda writes its own logs)
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.ai_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Custom policy for logs (read app log group), S3 (write summaries), DynamoDB (write metadata), SNS (publish)
resource "aws_iam_policy" "ai_lambda_policy" {
  name        = "${local.name_prefix}-ai-lambda-policy"
  description = "Least-privilege permissions for AI log summarizer Lambda"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "LogsReadFromAppLogGroup"
        Effect = "Allow"
        Action = [
          "logs:FilterLogEvents",
          "logs:GetLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:${aws_cloudwatch_log_group.app_logs.name}:*"
      },
      {
        Sid    = "S3WriteSummaries"
        Effect = "Allow"
        Action = [
          "s3:PutObject"
        ]
        Resource = "arn:aws:s3:::${aws_s3_bucket.ai_logs.bucket}/summaries/*"
      },
      {
        Sid    = "DynamoWriteMetadata"
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem"
        ]
        Resource = "arn:aws:dynamodb:${var.aws_region}:${data.aws_caller_identity.current.account_id}:table/${aws_dynamodb_table.ai_log_summaries.name}"
      },
      {
        Sid    = "SnsPublish"
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = aws_sns_topic.alerts.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ai_lambda_policy_attach" {
  role       = aws_iam_role.ai_lambda_role.name
  policy_arn = aws_iam_policy.ai_lambda_policy.arn
}
