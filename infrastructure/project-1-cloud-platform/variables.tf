##############################################
#  Global Variables
##############################################

variable "aws_region" {
  description = "AWS region to deploy RSVP Cloud Platform"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Name prefix for all RSVP resources"
  type        = string
  default     = "rsvp"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

##############################################
#  Cost / Deployment Toggles
##############################################

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway for private subnet egress (expensive). Default false for demo deploys."
  type        = bool
  default     = false
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
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default = [
    "10.0.1.0/24",
    "10.0.2.0/24",
  ]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default = [
    "10.0.3.0/24",
    "10.0.4.0/24",
  ]
}

##############################################
#  EC2 / App Settings
##############################################

variable "instance_type" {
  description = "EC2 instance type for the web app"
  type        = string
  default     = "t3.micro"
}

variable "allowed_http_cidrs" {
  description = "CIDR blocks allowed to reach HTTP (ALB)"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

##############################################
#  RDS Settings
##############################################

variable "rds_engine" {
  description = "Database engine"
  type        = string
  default     = "mysql"
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

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "rsvpadmin"
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
  validation {
    condition     = length(var.db_password) >= 12
    error_message = "Database password must be at least 12 characters."
  }
}

variable "db_name" {
  description = "Application database name"
  type        = string
  default     = "rsvp_app"
}

##############################################
#  AI / External APIs
##############################################

variable "openai_api_key" {
  description = "OpenAI API key for AI log summarization"
  type        = string
  sensitive   = true
  validation {
    condition     = length(var.openai_api_key) > 0
    error_message = "OpenAI API key is required."
  }
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

variable "enable_lambda_error_alarm" {
  description = "Create an alarm on AI Lambda Errors metric"
  type        = bool
  default     = true
}

