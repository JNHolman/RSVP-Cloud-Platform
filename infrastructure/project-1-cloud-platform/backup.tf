##############################################
# AWS Backup — independent recovery layer
##############################################
resource "aws_kms_key" "backup" {
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
  description             = "KMS key for RSVP AWS Backup vault"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  # Recovery artifacts outlive the primary resource. Prevent Terraform from
  # scheduling deletion of the key that is required to restore them.
  lifecycle {
    prevent_destroy = true
  }
  tags = { Name = "${local.name_prefix}-backup-kms" }
}

resource "aws_backup_vault" "production" {
  name        = "${local.name_prefix}-recovery"
  kms_key_arn = aws_kms_key.backup.arn
  tags = { Purpose = "disaster-recovery" }
}

# Governance mode protects production recovery points from routine or accidental
# deletion while remaining reversible by appropriately privileged administrators.
# Omitting changeable_for_days intentionally avoids irreversible compliance mode.
resource "aws_backup_vault_lock_configuration" "production" {
  count = var.environment == "prod" ? 1 : 0

  backup_vault_name  = aws_backup_vault.production.name
  min_retention_days = 7
  max_retention_days = 35
}

resource "aws_backup_plan" "production" {
  name = "${local.name_prefix}-recovery-plan"

  rule {
    rule_name         = "daily-rds-backup"
    target_vault_name = aws_backup_vault.production.name
    schedule          = "cron(0 5 ? * * *)"

    lifecycle {
      delete_after = 35
    }

    recovery_point_tags = {
      Project     = var.project_name
      Environment = var.environment
      Recovery    = "daily"
    }
  }
}

resource "aws_iam_role" "backup" {
  name = "${local.name_prefix}-backup-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { Service = "backup.amazonaws.com" }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "backup" {
  role       = aws_iam_role.backup.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup"
}

resource "aws_iam_role_policy_attachment" "backup_restore" {
  role       = aws_iam_role.backup.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForRestores"
}

resource "aws_backup_selection" "rds" {
  iam_role_arn = aws_iam_role.backup.arn
  name         = "${local.name_prefix}-rds"
  plan_id      = aws_backup_plan.production.id
  resources    = [aws_db_instance.app_db.arn]

  # Avoid a first-apply race where the selection is created before the
  # service role has the policies AWS Backup needs to back up and restore RDS.
  depends_on = [
    aws_iam_role_policy_attachment.backup,
    aws_iam_role_policy_attachment.backup_restore,
  ]
}
