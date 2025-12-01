##############################################
#  RDS – Database Layer for RSVP App
##############################################

# Security group for RDS – only allow app tier
resource "aws_security_group" "rds_sg" {
  name        = "${var.project_name}-${var.environment}-rds-sg"
  description = "Security group for RSVP RDS database"
  vpc_id      = aws_vpc.main.id

  # Allow MySQL from app instances only
  ingress {
    description = "MySQL from app security group"
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    security_groups = [
      aws_security_group.app_sg.id
    ]
  }

  # Outbound allowed (for patches, monitoring, etc.)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-rds-sg"
    Environment = var.environment
    Project     = var.project_name
    Tier        = "db"
  }
}

##############################################
#  DB Subnet Group – RDS only in private subnets
##############################################

resource "aws_db_subnet_group" "rds" {
  name       = "${var.project_name}-${var.environment}-rds-subnets"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name        = "${var.project_name}-${var.environment}-rds-subnets"
    Environment = var.environment
    Project     = var.project_name
    Tier        = "db"
  }
}

##############################################
#  RDS MySQL Instance
##############################################

# NOTE: For a real environment, use SSM or secrets manager.
# For this portfolio + lab, keep it simple and controlled.

resource "aws_db_instance" "rsvp_db" {
  identifier = "${var.project_name}-${var.environment}-db"

  engine               = var.rds_engine          # default "mysql"
  instance_class       = var.rds_instance_class  # default "db.t3.micro"
  allocated_storage    = var.rds_allocated_storage
  storage_encrypted    = true
  multi_az             = true
  publicly_accessible  = false

  username = "rsvp_admin"
  password = "ChangeMeStrongPassword123!"

  db_subnet_group_name   = aws_db_subnet_group.rds.name
  vpc_security_group_ids = [aws_security_group.rds_sg.id]

  backup_retention_period = 7
  skip_final_snapshot     = true

  deletion_protection     = false

  auto_minor_version_upgrade = true

  tags = {
    Name        = "${var.project_name}-${var.environment}-rds"
    Environment = var.environment
    Project     = var.project_name
    Tier        = "db"
  }
}

##############################################
#  RDS Outputs
##############################################

output "rds_endpoint" {
  description = "RDS endpoint for application connection"
  value       = aws_db_instance.rsvp_db.endpoint
}

output "rds_db_name" {
  description = "RDS database identifier"
  value       = aws_db_instance.rsvp_db.id
}
