terraform {
  # Match your installed Terraform (1.0.11) instead of forcing 1.6+
  required_version = ">= 1.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.67.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.4.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}
