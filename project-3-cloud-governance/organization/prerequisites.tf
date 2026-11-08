resource "terraform_data" "account_creation_prerequisites" {
  count = var.create_member_accounts ? 1 : 0

  input = var.member_account_emails

  lifecycle {
    precondition {
      condition     = alltrue([for email in values(var.member_account_emails) : trimspace(email) != ""])
      error_message = "create_member_accounts=true requires a non-empty root email for every member account."
    }

    precondition {
      condition     = length(distinct(values(var.member_account_emails))) == length(values(var.member_account_emails))
      error_message = "Every member account must use a unique root email address."
    }
  }
}

resource "terraform_data" "delegated_admin_prerequisites" {
  count = var.configure_delegated_admins ? 1 : 0

  input = local.account_ids

  lifecycle {
    precondition {
      condition     = can(regex("^[0-9]{12}$", local.account_ids.security))
      error_message = "configure_delegated_admins=true requires a valid Security account ID."
    }

    precondition {
      condition     = can(regex("^[0-9]{12}$", local.account_ids.shared_services))
      error_message = "configure_delegated_admins=true requires a valid Shared Services account ID."
    }
  }
}
