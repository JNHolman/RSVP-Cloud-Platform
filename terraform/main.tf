##############################################
#  Terraform Root Configuration
##############################################

terraform {
  required_version = ">= 1.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }

  # Local backend — easier for personal projects
  backend "local" {
    path = "terraform.tfstate"
  }
}

##############################################
#  AWS Provider Configuration
##############################################

provider "aws" {
  region = var.aws_region
}

