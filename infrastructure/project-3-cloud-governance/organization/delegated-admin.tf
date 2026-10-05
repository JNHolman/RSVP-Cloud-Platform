resource "aws_guardduty_organization_admin_account" "security" {
  count = var.configure_delegated_admins ? 1 : 0
  admin_account_id = local.account_ids.security

  depends_on = [aws_organizations_organization.this, terraform_data.delegated_admin_prerequisites]
}

resource "aws_securityhub_organization_admin_account" "security" {
  count = var.configure_delegated_admins ? 1 : 0
  admin_account_id = local.account_ids.security

  depends_on = [aws_organizations_organization.this, terraform_data.delegated_admin_prerequisites]
}

resource "aws_organizations_delegated_administrator" "config_rules" {
  count = var.configure_delegated_admins ? 1 : 0
  account_id        = local.account_ids.security
  service_principal = "config-multiaccountsetup.amazonaws.com"

  depends_on = [aws_organizations_organization.this, terraform_data.delegated_admin_prerequisites]
}

resource "aws_organizations_delegated_administrator" "config_aggregator" {
  count = var.configure_delegated_admins ? 1 : 0
  account_id        = local.account_ids.security
  service_principal = "config.amazonaws.com"

  depends_on = [aws_organizations_organization.this, terraform_data.delegated_admin_prerequisites]
}

resource "aws_organizations_delegated_administrator" "stacksets" {
  count = var.configure_delegated_admins && var.stacksets_trusted_access_activated ? 1 : 0
  account_id        = local.account_ids.shared_services
  service_principal = "member.org.stacksets.cloudformation.amazonaws.com"

  depends_on = [aws_organizations_organization.this, terraform_data.delegated_admin_prerequisites]
}
