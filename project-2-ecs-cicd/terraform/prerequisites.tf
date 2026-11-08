# Fail invalid scaling relationships during planning instead of allowing AWS to
# reject an otherwise syntactically valid configuration during deployment.
resource "terraform_data" "input_contracts" {
  lifecycle {
    precondition {
      condition     = var.ecs_min_capacity >= 1
      error_message = "ecs_min_capacity must be at least 1 for this continuously available service."
    }

    precondition {
      condition     = var.ecs_max_capacity >= var.ecs_min_capacity
      error_message = "ecs_max_capacity must be greater than or equal to ecs_min_capacity."
    }
  }
}
