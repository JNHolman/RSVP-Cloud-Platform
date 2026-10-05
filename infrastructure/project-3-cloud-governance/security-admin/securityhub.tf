resource "aws_securityhub_account" "organization" {
  enable_default_standards = true
}

resource "aws_securityhub_organization_configuration" "organization" {
  auto_enable = true

  depends_on = [aws_securityhub_account.organization]
}
