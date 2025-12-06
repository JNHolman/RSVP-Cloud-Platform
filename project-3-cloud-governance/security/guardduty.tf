resource "aws_guardduty_detector" "main" {
  enable = true

  tags = merge(
    var.tags,
    {
      "Component" = "security"
      "Service"   = "GuardDuty"
    }
  )
}

# Optional later: custom publishing / auto-enable for member accounts in real org
