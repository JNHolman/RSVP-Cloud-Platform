terraform {
  required_version = ">= 1.6.0, < 2.0.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.65.0" }
    archive = { source = "hashicorp/archive", version = "~> 2.4.0" }
  }
}
provider "aws" {
  region = var.aws_region
  default_tags { tags = local.standard_tags }
}
locals {
  standard_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
    Owner       = "Josh-Holman"
    Repository  = "RSVP-Cloud-Platform"
  }
}
data "aws_caller_identity" "current" {}
