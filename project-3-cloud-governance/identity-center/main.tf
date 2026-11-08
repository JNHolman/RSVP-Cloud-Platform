data "aws_ssoadmin_instances" "this" {}

locals {
  identity_center_instances = tolist(data.aws_ssoadmin_instances.this.arns)
  instance_arn              = try(one(local.identity_center_instances), null)
  readonly_accounts = {
    security        = var.account_ids.security
    log_archive     = var.account_ids.log_archive
    shared_services = var.account_ids.shared_services
    nonprod         = var.account_ids.nonprod
    prod            = var.account_ids.prod
  }
  platform_accounts = {
    shared_services = var.account_ids.shared_services
    nonprod         = var.account_ids.nonprod
    prod            = var.account_ids.prod
  }
}

resource "aws_ssoadmin_permission_set" "administrator" {
  name             = "CloudAdministrator"
  description      = "Privileged cloud administration; assign sparingly."
  instance_arn     = local.instance_arn
  session_duration = "PT2H"

  lifecycle {
    precondition {
      condition     = length(local.identity_center_instances) == 1
      error_message = "IAM Identity Center must be enabled in this AWS Organization before applying this stack."
    }
  }
}

resource "aws_ssoadmin_managed_policy_attachment" "administrator" {
  instance_arn       = local.instance_arn
  permission_set_arn = aws_ssoadmin_permission_set.administrator.arn
  managed_policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}

resource "aws_ssoadmin_permission_set" "platform" {
  name             = "PlatformOperator"
  description      = "Day-to-day platform engineering access without IAM administration."
  instance_arn     = local.instance_arn
  session_duration = "PT4H"

  lifecycle {
    precondition {
      condition     = length(local.identity_center_instances) == 1
      error_message = "IAM Identity Center must be enabled in this AWS Organization before applying this stack."
    }
  }
}

resource "aws_ssoadmin_managed_policy_attachment" "platform" {
  instance_arn       = local.instance_arn
  permission_set_arn = aws_ssoadmin_permission_set.platform.arn
  managed_policy_arn = "arn:aws:iam::aws:policy/PowerUserAccess"
}

resource "aws_ssoadmin_permission_set" "readonly" {
  name             = "EngineeringReadOnly"
  description      = "Read-only engineering and audit access."
  instance_arn     = local.instance_arn
  session_duration = "PT8H"

  lifecycle {
    precondition {
      condition     = length(local.identity_center_instances) == 1
      error_message = "IAM Identity Center must be enabled in this AWS Organization before applying this stack."
    }
  }
}

resource "aws_ssoadmin_managed_policy_attachment" "readonly" {
  instance_arn       = local.instance_arn
  permission_set_arn = aws_ssoadmin_permission_set.readonly.arn
  managed_policy_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
}

resource "aws_ssoadmin_account_assignment" "security_admin" {
  instance_arn       = local.instance_arn
  permission_set_arn = aws_ssoadmin_permission_set.administrator.arn
  principal_id       = var.admin_group_id
  principal_type     = "GROUP"
  target_id          = var.account_ids.security
  target_type        = "AWS_ACCOUNT"

  depends_on = [aws_ssoadmin_managed_policy_attachment.administrator]
}

resource "aws_ssoadmin_account_assignment" "platform" {
  for_each = local.platform_accounts

  instance_arn       = local.instance_arn
  permission_set_arn = aws_ssoadmin_permission_set.platform.arn
  principal_id       = var.platform_group_id
  principal_type     = "GROUP"
  target_id          = each.value
  target_type        = "AWS_ACCOUNT"

  depends_on = [aws_ssoadmin_managed_policy_attachment.platform]
}

resource "aws_ssoadmin_account_assignment" "readonly" {
  for_each = local.readonly_accounts

  instance_arn       = local.instance_arn
  permission_set_arn = aws_ssoadmin_permission_set.readonly.arn
  principal_id       = var.readonly_group_id
  principal_type     = "GROUP"
  target_id          = each.value
  target_type        = "AWS_ACCOUNT"

  depends_on = [aws_ssoadmin_managed_policy_attachment.readonly]
}
