##############################################
#  RDS Subnet Group & Security Group
##############################################

# Use the private subnets for the DB
resource "aws_db_subnet_group" "rsvp_db_subnets" {
  name = "${var.project_name}-${var.environment}-db-subnets"
  subnet_ids = [
    aws_subnet.private[0].id,
    aws_subnet.private[1].id
  ]

  tags = {
    Name        = "${var.project_name}-${var.environment}-db-subnets"
    Project     = var.project_name
    Environment = var.environment
  }
}

# DB security group – allow MySQL from app instances only
resource "aws_security_group" "db_sg" {
  name        = "${var.project_name}-${var.environment}-db-sg"
  description = "Allow MySQL from app instances"
  # grab VPC ID from one of the private subnets so we don't depend on the VPC name
  vpc_id = aws_subnet.private[0].vpc_id

  ingress {
    description     = "MySQL from app instances"
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.app_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-db-sg"
    Project     = var.project_name
    Environment = var.environment
  }
}

##############################################
#  RDS instance
##############################################

resource "aws_db_instance" "rsvp_db" {
  identifier        = "${var.project_name}-${var.environment}-db"
  engine            = "mysql"
  engine_version    = "8.0"
  instance_class    = "db.t3.micro"
  allocated_storage = 20
  username          = var.db_username
  password          = var.db_password
  db_name           = var.db_name
  port              = 3306

  db_subnet_group_name   = aws_db_subnet_group.rsvp_db_subnets.name
  vpc_security_group_ids = [aws_security_group.db_sg.id]

  backup_retention_period = 1
  skip_final_snapshot     = true

  deletion_protection = false

  tags = {
    Name        = "${var.project_name}-${var.environment}-db"
    Project     = var.project_name
    Environment = var.environment
  }
}

