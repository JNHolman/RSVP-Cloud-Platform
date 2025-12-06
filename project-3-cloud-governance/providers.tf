terraform {
  # Compatible with your local 1.0.11, but still sane for the project
  required_version = ">= 1.0.0, < 1.4.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      # AWS provider 5.x needs newer Terraform, so use 4.x here
      version = "~> 4.0"
    }
  }

  # If/when you add an S3 backend, keep it here (commented for now)
  # backend "s3" {
  #   bucket = "YOUR-TERRAFORM-STATE-BUCKET"
  #   key    = "project-3-cloud-governance/terraform.tfstate"
  #   region = "us-east-1"
  # }
}

provider "aws" {
  region = var.aws_region
}

provider "aws" {
  alias  = "security"
  region = var.aws_region
}

provider "aws" {
  alias  = "logging"
  region = var.aws_region
}

provider "aws" {
  alias  = "workload"
  region = var.aws_region
}
