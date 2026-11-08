variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"
  validation {
    condition     = contains(["dev", "stage", "prod"], var.environment)
    error_message = "environment must be dev, stage, or prod."
  }
}

variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Prefix for all ECS Project 2 resources"
  type        = string
  default     = "rsvp-project2"

  validation {
    condition     = can(regex("^[a-z0-9]([a-z0-9-]{0,20}[a-z0-9])?$", var.project_name))
    error_message = "project_name must be 1-22 characters, use lowercase letters/numbers/hyphens only, and start/end with a letter or number."
  }
}

variable "container_image" {
  description = "Immutable ECR image URI for the ECS service. Use a sha256 digest or a full 40-character Git SHA tag."
  type        = string

  validation {
    condition = can(regex(
      "^[0-9]{12}\\.dkr\\.ecr\\.[a-z0-9-]+\\.amazonaws\\.com(\\.cn)?/[a-z0-9]+([._/-][a-z0-9]+)*(@sha256:[0-9a-fA-F]{64}|:[0-9a-fA-F]{40})$",
      var.container_image
    ))
    error_message = "container_image must be an Amazon ECR URI ending with @sha256:<64 hex characters> or :<40-character Git SHA>; mutable tags and non-ECR registries are not allowed."
  }
}

variable "domain_name" {
  description = "DNS name for the ECS application, for example service.example.com"
  type        = string
}

variable "route53_zone_id" {
  description = "Route53 hosted-zone ID containing domain_name"
  type        = string
}

variable "ecs_min_capacity" {
  description = "Minimum and steady-state ECS task count across availability zones"
  type        = number
  default     = 2
}

variable "ecs_max_capacity" {
  description = "Maximum ECS task count for service autoscaling"
  type        = number
  default     = 6
}

variable "ecs_cpu_target" {
  description = "Target average ECS service CPU utilization percentage"
  type        = number
  default     = 60

  validation {
    condition     = var.ecs_cpu_target >= 10 && var.ecs_cpu_target <= 90
    error_message = "ecs_cpu_target must be between 10 and 90 percent."
  }
}

variable "ecs_memory_target" {
  description = "Target average ECS service memory utilization percentage"
  type        = number
  default     = 70

  validation {
    condition     = var.ecs_memory_target >= 10 && var.ecs_memory_target <= 90
    error_message = "ecs_memory_target must be between 10 and 90 percent."
  }
}

variable "alert_email" {
  description = "Optional email endpoint for production operational alarms"
  type        = string
  default     = ""
}

variable "log_retention_days" {
  description = "CloudWatch log retention period"
  type        = number
  default     = 30

  validation {
    condition = contains([
      1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731,
      1096, 1827, 2192, 2557, 2922, 3288, 3653,
    ], var.log_retention_days)
    error_message = "log_retention_days must be a CloudWatch Logs supported retention value."
  }
}
