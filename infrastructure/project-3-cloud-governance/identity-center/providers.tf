provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = "identity"
      ManagedBy   = "Terraform"
      Owner       = var.owner
    }
  }
}
