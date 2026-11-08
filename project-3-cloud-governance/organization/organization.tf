locals {
  base_service_access_principals = [
    "cloudtrail.amazonaws.com",
    "guardduty.amazonaws.com",
    "securityhub.amazonaws.com",
    "config.amazonaws.com",
    "config-multiaccountsetup.amazonaws.com",
    # Preserve IAM Identity Center trusted access across organization applies.
    # The Identity Center instance itself must still be enabled with the
    # Identity Center service/console before its Terraform stack is applied.
    "sso.amazonaws.com",
  ]
}

resource "aws_organizations_organization" "this" {
  feature_set = "ALL"

  enabled_policy_types = [
    "SERVICE_CONTROL_POLICY"
  ]

  # CloudFormation StackSets trusted access must first be activated through
  # CloudFormation so AWS can create its required service-linked role. Once
  # that is done, opt in here so Terraform preserves the trusted-access
  # principal instead of trying to bootstrap it generically through Organizations.
  aws_service_access_principals = concat(
    local.base_service_access_principals,
    var.stacksets_trusted_access_activated ? ["stacksets.cloudformation.amazonaws.com"] : []
  )
}

resource "aws_organizations_organizational_unit" "security" {
  name      = "Security"
  parent_id = aws_organizations_organization.this.roots[0].id
}

resource "aws_organizations_organizational_unit" "infrastructure" {
  name      = "Infrastructure"
  parent_id = aws_organizations_organization.this.roots[0].id
}

resource "aws_organizations_organizational_unit" "workloads" {
  name      = "Workloads"
  parent_id = aws_organizations_organization.this.roots[0].id
}

resource "aws_organizations_organizational_unit" "nonprod" {
  name      = "NonProd"
  parent_id = aws_organizations_organizational_unit.workloads.id
}

resource "aws_organizations_organizational_unit" "prod" {
  name      = "Prod"
  parent_id = aws_organizations_organizational_unit.workloads.id
}
