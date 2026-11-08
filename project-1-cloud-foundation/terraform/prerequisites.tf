# Cross-variable input contracts that cannot be expressed safely as independent
# variable validation in the Terraform 1.6 baseline used by this repository.
resource "terraform_data" "input_contracts" {
  lifecycle {
    precondition {
      condition     = var.rds_allocated_storage >= 20
      error_message = "rds_allocated_storage must be at least 20 GiB for this MySQL gp3 baseline."
    }

    precondition {
      condition     = var.rds_max_allocated_storage >= ceil(var.rds_allocated_storage * 1.10)
      error_message = "rds_max_allocated_storage must be at least 10% greater than rds_allocated_storage when RDS storage autoscaling is enabled."
    }

    precondition {
      condition = length(distinct(concat(
        var.public_subnet_cidrs,
        var.private_subnet_cidrs,
      ))) == 4
      error_message = "public_subnet_cidrs and private_subnet_cidrs must contain four distinct CIDR blocks in total."
    }
  }
}
