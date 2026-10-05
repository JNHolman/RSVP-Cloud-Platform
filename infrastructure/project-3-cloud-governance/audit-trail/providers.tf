provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = "organization-audit"
      ManagedBy   = "Terraform"
      Owner       = var.owner
    }
  }
}
