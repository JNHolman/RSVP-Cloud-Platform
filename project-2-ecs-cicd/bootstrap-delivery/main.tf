data "tls_certificate" "github_actions" {
  url = "https://token.actions.githubusercontent.com"
}

resource "aws_iam_openid_connect_provider" "github_actions" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.github_actions.certificates[0].sha1_fingerprint]
}

resource "aws_kms_key" "ecr" {
  # Explicitly retain account-root administration so IAM policies in this
  # account can delegate key use to approved AWS services and roles.
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "EnableAccountAdministration"
      Effect    = "Allow"
      Principal = { AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root" }
      Action    = "kms:*"
      Resource  = "*"
    }]
  })
  description             = "Customer-managed KMS key for RSVP Project 2 container images"
  enable_key_rotation     = true
  deletion_window_in_days = 30

  tags = { Purpose = "ecr-image-encryption" }
}

resource "aws_kms_alias" "ecr" {
  name          = "alias/${var.project_name}-ecr"
  target_key_id = aws_kms_key.ecr.key_id
}

resource "aws_ecr_repository" "app" {
  for_each             = var.environments
  name                 = "${var.project_name}-${each.key}-app"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = aws_kms_key.ecr.arn
  }
}

resource "aws_ecr_lifecycle_policy" "app" {
  for_each   = aws_ecr_repository.app
  repository = each.value.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Retain the most recent immutable application images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 50
      }
      action = { type = "expire" }
    }]
  })
}

data "aws_iam_policy_document" "github_deploy_assume" {
  for_each = var.environments

  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github_actions.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_repository}:environment:${each.key}"]
    }
  }
}

resource "aws_iam_role" "github_deploy" {
  for_each           = var.environments
  name               = "${var.project_name}-${each.key}-github-deploy"
  assume_role_policy = data.aws_iam_policy_document.github_deploy_assume[each.key].json
}

data "aws_iam_policy_document" "github_deploy" {
  for_each = var.environments

  statement {
    sid = "EcrPush"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:BatchGetImage",
      "ecr:CompleteLayerUpload",
      "ecr:DescribeImages",
      "ecr:GetDownloadUrlForLayer",
      "ecr:InitiateLayerUpload",
      "ecr:PutImage",
      "ecr:UploadLayerPart",
    ]
    resources = [aws_ecr_repository.app[each.key].arn]
  }

  statement {
    sid       = "EcrLogin"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  # List/DescribeTaskDefinition do not support resource-level permissions.
  statement {
    sid = "EcsTaskDefinitionRead"
    actions = [
      "ecs:DescribeTaskDefinition",
      "ecs:ListTaskDefinitions",
    ]
    resources = ["*"]
  }

  # RegisterTaskDefinition supports the task-definition resource type, so limit
  # deployment writes to the environment-specific task-definition family.
  statement {
    sid     = "EcsTaskDefinitionRegister"
    actions = ["ecs:RegisterTaskDefinition"]
    resources = [
      "arn:aws:ecs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:task-definition/${var.project_name}-${each.key}-task:*"
    ]
  }

  statement {
    sid = "EcsServiceDeploy"
    actions = [
      "ecs:DescribeServices",
      "ecs:UpdateService",
    ]
    resources = [
      "arn:aws:ecs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:service/${var.project_name}-${each.key}-cluster/${var.project_name}-${each.key}-service"
    ]
  }

  # These role ARNs are deterministic and may be referenced before the runtime
  # stack creates them. This breaks the first-image bootstrap dependency without
  # granting PassRole to unrelated IAM roles.
  statement {
    sid     = "PassEcsRoles"
    actions = ["iam:PassRole"]
    resources = [
      "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.project_name}-${each.key}-task-execution-role",
      "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.project_name}-${each.key}-task-role",
    ]

    condition {
      test     = "StringEquals"
      variable = "iam:PassedToService"
      values   = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy" "github_deploy" {
  for_each = var.environments
  name     = "${var.project_name}-${each.key}-deploy"
  role     = aws_iam_role.github_deploy[each.key].id
  policy   = data.aws_iam_policy_document.github_deploy[each.key].json
}
