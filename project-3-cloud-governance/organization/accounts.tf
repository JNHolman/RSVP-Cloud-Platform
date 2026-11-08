resource "aws_organizations_account" "security" {
  count     = var.create_member_accounts ? 1 : 0
  name      = "RSVP Security"
  email     = var.member_account_emails.security
  parent_id = aws_organizations_organizational_unit.security.id
  role_name = var.account_access_role_name

  lifecycle {
    prevent_destroy = true
  }

  depends_on = [terraform_data.account_creation_prerequisites]
}

resource "aws_organizations_account" "log_archive" {
  count     = var.create_member_accounts ? 1 : 0
  name      = "RSVP Log Archive"
  email     = var.member_account_emails.log_archive
  parent_id = aws_organizations_organizational_unit.security.id
  role_name = var.account_access_role_name

  lifecycle {
    prevent_destroy = true
  }

  depends_on = [terraform_data.account_creation_prerequisites]
}

resource "aws_organizations_account" "shared_services" {
  count     = var.create_member_accounts ? 1 : 0
  name      = "RSVP Shared Services"
  email     = var.member_account_emails.shared_services
  parent_id = aws_organizations_organizational_unit.infrastructure.id
  role_name = var.account_access_role_name

  lifecycle {
    prevent_destroy = true
  }

  depends_on = [terraform_data.account_creation_prerequisites]
}

resource "aws_organizations_account" "nonprod" {
  count     = var.create_member_accounts ? 1 : 0
  name      = "RSVP NonProd"
  email     = var.member_account_emails.nonprod
  parent_id = aws_organizations_organizational_unit.nonprod.id
  role_name = var.account_access_role_name

  lifecycle {
    prevent_destroy = true
  }

  depends_on = [terraform_data.account_creation_prerequisites]
}

resource "aws_organizations_account" "prod" {
  count     = var.create_member_accounts ? 1 : 0
  name      = "RSVP Prod"
  email     = var.member_account_emails.prod
  parent_id = aws_organizations_organizational_unit.prod.id
  role_name = var.account_access_role_name

  lifecycle {
    prevent_destroy = true
  }

  depends_on = [terraform_data.account_creation_prerequisites]
}

locals {
  account_ids = {
    security        = var.create_member_accounts ? aws_organizations_account.security[0].id : var.existing_account_ids.security
    log_archive     = var.create_member_accounts ? aws_organizations_account.log_archive[0].id : var.existing_account_ids.log_archive
    shared_services = var.create_member_accounts ? aws_organizations_account.shared_services[0].id : var.existing_account_ids.shared_services
    nonprod         = var.create_member_accounts ? aws_organizations_account.nonprod[0].id : var.existing_account_ids.nonprod
    prod            = var.create_member_accounts ? aws_organizations_account.prod[0].id : var.existing_account_ids.prod
  }
}
