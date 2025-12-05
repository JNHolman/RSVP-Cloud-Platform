resource "aws_db_subnet_group" "app_db_subnets" {
  name       = "${local.name_prefix}-db-subnets"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "${local.name_prefix}-db-subnet-group"
  }
}

resource "aws_db_instance" "app_db" {
  identifier        = "${local.name_prefix}-db"
  engine            = var.rds_engine
  instance_class    = var.rds_instance_class
  allocated_storage = var.rds_allocated_storage

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.app_db_subnets.name
  vpc_security_group_ids = [aws_security_group.db_sg.id]

  multi_az                = false
  publicly_accessible     = false
  skip_final_snapshot     = true
  deletion_protection     = false
  backup_retention_period = 1

  tags = {
    Name        = "${local.name_prefix}-rds"
    Environment = var.environment
    Project     = var.project_name
  }
}

