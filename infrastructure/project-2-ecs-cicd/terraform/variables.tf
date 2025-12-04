variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Prefix for all ECS Project 2 resources"
  type        = string
  default     = "rsvp-project2"
}

variable "container_image" {
  description = "ECR image URI for the ECS service"
  type        = string
  default = "852121054175.dkr.ecr.us-east-1.amazonaws.com/rsvp-project2-app:latest"
  }
