##############################################
#  Global Variables
##############################################

variable "aws_region" {
  description = "AWS region to deploy RSVP Cloud Platform"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Name prefix for all RSVP resources. Limited so generated ALB names remain within AWS's 32-character limit in every supported environment."
  type        = string
  default     = "rsvp"

  validation {
    condition     = can(regex("^[a-z0-9]([a-z0-9-]{0,20}[a-z0-9])?$", var.project_name))
    error_message = "project_name must be 1-22 characters, use lowercase letters/numbers/hyphens only, and start/end with a letter or number."
  }
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
  validation {
    condition     = contains(["dev", "stage", "prod"], var.environment)
    error_message = "environment must be dev, stage, or prod."
  }
}

##############################################
#  Networking
##############################################

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "Exactly two public-subnet CIDRs, one for each availability zone used by the ALB and NAT gateways."
  type        = list(string)
  default = [
    "10.0.1.0/24",
    "10.0.2.0/24",
  ]

  validation {
    condition     = length(var.public_subnet_cidrs) == 2 && length(distinct(var.public_subnet_cidrs)) == 2
    error_message = "public_subnet_cidrs must contain exactly two distinct CIDR blocks."
  }
}

variable "private_subnet_cidrs" {
  description = "Exactly two private-subnet CIDRs, one for each availability zone used by application and database workloads."
  type        = list(string)
  default = [
    "10.0.3.0/24",
    "10.0.4.0/24",
  ]

  validation {
    condition     = length(var.private_subnet_cidrs) == 2 && length(distinct(var.private_subnet_cidrs)) == 2
    error_message = "private_subnet_cidrs must contain exactly two distinct CIDR blocks."
  }
}

variable "allowed_http_cidrs" {
  description = "CIDR blocks allowed to reach the public ALB on HTTP/HTTPS"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "domain_name" {
  description = "DNS name for the production ALB, for example app.example.com"
  type        = string
}

variable "route53_zone_id" {
  description = "Route53 hosted-zone ID containing domain_name"
  type        = string
}

##############################################
#  EC2 / App Settings
##############################################

variable "instance_type" {
  description = "EC2 instance type for the web app"
  type        = string
  default     = "t3.micro"
}

##############################################
#  RDS Settings
##############################################

variable "rds_engine" {
  description = "Database engine. This stack intentionally supports MySQL only because its parameter and log-export controls are MySQL-specific."
  type        = string
  default     = "mysql"

  validation {
    condition     = var.rds_engine == "mysql"
    error_message = "rds_engine must be mysql for this stack."
  }
}

variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "rds_allocated_storage" {
  description = "RDS storage in GB"
  type        = number
  default     = 20
}

variable "rds_engine_version" {
  description = "MySQL engine major version; AWS-managed minor version upgrades remain enabled"
  type        = string
  default     = "8.0"
}

variable "rds_parameter_group_family" {
  description = "RDS parameter group family matching the selected engine major version"
  type        = string
  default     = "mysql8.0"
}

variable "rds_max_allocated_storage" {
  description = "Maximum RDS storage in GB when storage autoscaling is enabled"
  type        = number
  default     = 100
}

variable "rds_backup_retention_days" {
  description = "Number of days to retain automated RDS backups for point-in-time recovery"
  type        = number
  default     = 14

  validation {
    condition     = var.rds_backup_retention_days >= 7 && var.rds_backup_retention_days <= 35
    error_message = "Production backup retention must be between 7 and 35 days."
  }
}

variable "rds_backup_window" {
  description = "Daily UTC backup window"
  type        = string
  default     = "03:00-04:00"
}

variable "rds_maintenance_window" {
  description = "Weekly UTC maintenance window"
  type        = string
  default     = "Sun:05:00-Sun:06:00"
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "rsvpadmin"
}

variable "db_name" {
  description = "Application database name"
  type        = string
  default     = "rsvp_app"
}

##############################################
#  AI / External APIs
##############################################

variable "openai_secret_arn" {
  description = "Secrets Manager ARN containing the OpenAI API key; secret value is never stored in Terraform state"
  type        = string
  validation {
    condition     = can(regex("^arn:aws:secretsmanager:", var.openai_secret_arn))
    error_message = "openai_secret_arn must be an AWS Secrets Manager ARN."
  }
}

variable "ai_model" {
  description = "OpenAI model used for advisory operational analysis"
  type        = string
  default     = "gpt-5.5"
}

##############################################
#  Monitoring / Alerts
##############################################

variable "alert_email" {
  description = "Email address to receive CloudWatch / AI alerts (optional)"
  type        = string
  default     = ""
}

variable "alarm_alb_5xx_threshold" {
  description = "ALB 5XX count threshold per minute to trigger alarm"
  type        = number
  default     = 5
}

variable "alarm_asg_cpu_threshold" {
  description = "ASG average CPU threshold (%) to trigger alarm"
  type        = number
  default     = 75
}

variable "asg_cpu_target" {
  description = "Target average CPU utilization for EC2 Auto Scaling"
  type        = number
  default     = 60

  validation {
    condition     = var.asg_cpu_target >= 10 && var.asg_cpu_target <= 90
    error_message = "asg_cpu_target must be between 10 and 90."
  }
}

variable "enable_lambda_error_alarm" {
  description = "Create an alarm on AI Lambda Errors metric"
  type        = bool
  default     = true
}

variable "alarm_rds_cpu_threshold" {
  description = "RDS CPU percentage that triggers an operational alarm"
  type        = number
  default     = 80
}

variable "alarm_rds_free_storage_bytes" {
  description = "Minimum free RDS storage before alarming (bytes)"
  type        = number
  default     = 5368709120
}
