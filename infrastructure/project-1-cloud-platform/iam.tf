resource "aws_iam_role" "ec2_role" {
  name = "${local.name_prefix}-ec2-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{ Effect = "Allow", Principal = { Service = "ec2.amazonaws.com" }, Action = "sts:AssumeRole" }]
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

resource "aws_iam_role_policy_attachment" "ec2_cloudwatch_logs" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}

resource "aws_iam_role" "ai_lambda_role" {
  name = "${local.name_prefix}-ai-lambda-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{ Effect = "Allow", Principal = { Service = "lambda.amazonaws.com" }, Action = "sts:AssumeRole" }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.ai_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_xray" {
  role       = aws_iam_role.ai_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess"
}

resource "aws_iam_policy" "ai_lambda_policy" {
  name        = "${local.name_prefix}-ai-lambda-policy"
  description = "Least-privilege permissions for advisory AI operations analysis"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid = "ReadOpenAISecret", Effect = "Allow",
        Action = ["secretsmanager:GetSecretValue"], Resource = var.openai_secret_arn
      },
      {
        Sid = "LogsReadFromAppLogGroup", Effect = "Allow",
        Action = ["logs:FilterLogEvents"],
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:${aws_cloudwatch_log_group.app_logs.name}:*"
      },
      {
        Sid = "S3WriteSummaries", Effect = "Allow", Action = ["s3:PutObject"],
        Resource = "arn:aws:s3:::${aws_s3_bucket.ai_logs.bucket}/summaries/*"
      },
      {
        Sid = "KmsEncryptAIEvidence", Effect = "Allow",
        Action = ["kms:Encrypt", "kms:GenerateDataKey", "kms:DescribeKey"], Resource = aws_kms_key.ai_logs.arn
      },
      {
        Sid = "DynamoWriteMetadata", Effect = "Allow", Action = ["dynamodb:PutItem"],
        Resource = aws_dynamodb_table.ai_log_summaries.arn
      },
      {
        Sid = "SnsPublish", Effect = "Allow", Action = ["sns:Publish"], Resource = aws_sns_topic.alerts.arn
      },
      {
        Sid = "UseAlertTopicKmsKey", Effect = "Allow",
        Action = ["kms:Decrypt", "kms:GenerateDataKey*"], Resource = aws_kms_key.observability.arn
      },
      {
        Sid = "SendToAIDeadLetterQueue", Effect = "Allow", Action = ["sqs:SendMessage"],
        Resource = aws_sqs_queue.ai_analysis_dlq.arn
      },
      {
        Sid = "PublishAIOperationsMetrics", Effect = "Allow", Action = ["cloudwatch:PutMetricData"], Resource = "*",
        Condition = { StringEquals = { "cloudwatch:namespace" = "RSVP/AIOperations" } }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ai_lambda_policy_attach" {
  role       = aws_iam_role.ai_lambda_role.name
  policy_arn = aws_iam_policy.ai_lambda_policy.arn
}
