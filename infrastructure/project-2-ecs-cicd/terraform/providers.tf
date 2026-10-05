terraform {
  required_version = ">= 1.6.0, < 2.0.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.65.0" }
  }
}
provider "aws" {
  region = var.aws_region
  default_tags { tags = local.standard_tags }
}
locals {
  name_prefix = "${var.project_name}-${var.environment}"

  standard_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
    Owner       = "Josh-Holman"
    Repository  = "RSVP-Cloud-Platform"
  }
}
