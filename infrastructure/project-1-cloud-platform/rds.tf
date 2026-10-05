##############################################
# RDS encryption key
##############################################

resource "aws_kms_key" "rds" {
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
  description             = "KMS key for RSVP RDS storage, managed credentials, and Performance Insights"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  # Recovery artifacts outlive the primary resource. Prevent Terraform from
  # scheduling deletion of the key that is required to restore them.
  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Name = "${local.name_prefix}-rds-kms"
  }
}

resource "aws_kms_alias" "rds" {
  name          = "alias/${local.name_prefix}-rds"
  target_key_id = aws_kms_key.rds.key_id
}

##############################################
# Database subnet group
##############################################

resource "aws_db_subnet_group" "app_db_subnets" {
  name       = "${local.name_prefix}-db-subnets"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "${local.name_prefix}-db-subnet-group"
  }
}

##############################################
# MySQL parameter group
##############################################

resource "aws_db_parameter_group" "mysql" {
  name   = "${local.name_prefix}-mysql"
  family = var.rds_parameter_group_family

  parameter {
    name  = "require_secure_transport"
    value = "ON"
  }

  # Slow-query export is useful operational evidence without the volume and
  # sensitive-query exposure of MySQL general logging. RDS requires FILE output
  # for slow-query records to be published to CloudWatch Logs.
  parameter {
    name  = "slow_query_log"
    value = "1"
  }

  parameter {
    name  = "log_output"
    value = "FILE"
  }

  tags = {
    Name = "${local.name_prefix}-mysql-parameters"
  }
}

##############################################
# Production RDS instance
##############################################

resource "aws_iam_role" "rds_monitoring" {
  name = "${local.name_prefix}-rds-monitoring"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "monitoring.rds.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  role       = aws_iam_role.rds_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

resource "aws_db_instance" "app_db" {
  #checkov:skip=CKV_AWS_293:Deletion protection is enabled in prod; dev/stage retain final snapshots but remain intentionally tear-down capable.
  identifier = "${local.name_prefix}-db"

  depends_on = [
    aws_cloudwatch_log_group.rds_exports,
    aws_iam_role_policy_attachment.rds_monitoring,
  ]

  engine         = var.rds_engine
  engine_version = var.rds_engine_version
  instance_class = var.rds_instance_class

  allocated_storage     = var.rds_allocated_storage
  max_allocated_storage = var.rds_max_allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = true
  kms_key_id            = aws_kms_key.rds.arn

  db_name  = var.db_name
  username = var.db_username

  # RDS generates, stores, and rotates the master credential in Secrets Manager.
  # No database password is supplied through Terraform variables.
  manage_master_user_password   = true
  master_user_secret_kms_key_id = aws_kms_key.rds.arn

  db_subnet_group_name   = aws_db_subnet_group.app_db_subnets.name
  vpc_security_group_ids = [aws_security_group.db_sg.id]
  parameter_group_name   = aws_db_parameter_group.mysql.name

  multi_az            = true
  publicly_accessible               = false
  iam_database_authentication_enabled = true

  monitoring_interval = 60
  monitoring_role_arn = aws_iam_role.rds_monitoring.arn

  backup_retention_period = var.rds_backup_retention_days
  backup_window           = var.rds_backup_window
  maintenance_window      = var.rds_maintenance_window
  copy_tags_to_snapshot   = true

  deletion_protection       = var.environment == "prod"
  skip_final_snapshot       = false
  final_snapshot_identifier = "${local.name_prefix}-final-${formatdate("YYYYMMDDhhmmss", timestamp())}"
  delete_automated_backups  = false

  auto_minor_version_upgrade = true
  apply_immediately           = false

  enabled_cloudwatch_logs_exports = [
    "error",
    "slowquery",
  ]

  performance_insights_enabled          = true
  performance_insights_retention_period = 7
  performance_insights_kms_key_id       = aws_kms_key.rds.arn

  tags = {
    Name        = "${local.name_prefix}-rds"
    Environment = var.environment
    Project     = var.project_name
  }

  lifecycle {
    # timestamp() is used only to allocate a unique final snapshot name when a
    # DB resource is first created. Freeze it afterward to avoid perpetual diff.
    ignore_changes = [final_snapshot_identifier]
  }
}
