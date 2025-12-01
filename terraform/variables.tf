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
  default     = [
    "10.0.1.0/24",
    "10.0.2.0/24"
  ]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = [
    "10.0.3.0/24",
    "10.0.4.0/24"
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
  description = "CIDR blocks allowed to reach HTTP/HTTPS (ALB)"
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
