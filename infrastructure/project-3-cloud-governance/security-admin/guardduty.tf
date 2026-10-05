resource "aws_guardduty_detector" "organization" {
  enable = true
}

resource "aws_guardduty_organization_configuration" "organization" {
  detector_id                      = aws_guardduty_detector.organization.id
  auto_enable_organization_members = "ALL"
}
