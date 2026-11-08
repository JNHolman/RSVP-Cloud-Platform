resource "terraform_data" "dashboard_reader_prerequisites" {
  input = {
    account_id = var.dashboard_reader_account_id
    role_name  = var.dashboard_reader_role_name
  }

  lifecycle {
    precondition {
      condition = (
        (var.dashboard_reader_account_id == "" && var.dashboard_reader_role_name == "") ||
        (var.dashboard_reader_account_id != "" && var.dashboard_reader_role_name != "")
      )
      error_message = "dashboard_reader_account_id and dashboard_reader_role_name must either both be set or both be empty."
    }
  }
}
