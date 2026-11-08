terraform {
  required_version = ">= 1.6.0, < 2.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.65.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project    = var.project_name
      ManagedBy  = "Terraform"
      Owner      = "Josh-Holman"
      Repository = "RSVP-Cloud-Platform"
      Component  = "DeliveryBootstrap"
    }
  }
}

data "aws_caller_identity" "current" {}
