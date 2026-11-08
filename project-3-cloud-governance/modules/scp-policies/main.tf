terraform {
  required_version = ">= 1.6.0, < 2.0.0"
}

variable "protected_admin_role_patterns" {
  description = "Explicit account-scoped IAM role ARNs exempted from security-control SCP denies. Empty by default; wildcard account IDs are intentionally rejected."
  type        = list(string)
  default     = []

  validation {
    condition = alltrue([
      for arn in var.protected_admin_role_patterns :
      can(regex("^arn:(aws|aws-us-gov|aws-cn):iam::[0-9]{12}:role/.+$", arn)) && !strcontains(arn, "*") && !strcontains(arn, "?")
    ])
    error_message = "Each protected admin principal must be an explicit IAM role ARN with a 12-digit account ID; wildcards are not allowed."
  }
}

output "deny_leave_org" {
  value = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid      = "DenyLeavingOrganizationAndClosingAccount"
      Effect   = "Deny"
      Resource = "*"
      Action = [
        "organizations:LeaveOrganization",
        "account:CloseAccount",
      ]
    }]
  })
}

output "protect_security_controls" {
  value = jsonencode({
    Version = "2012-10-17"
    Statement = [merge({
      Sid      = "ProtectCentralSecurityControls"
      Effect   = "Deny"
      Resource = "*"
      Action = [
        "cloudtrail:DeleteTrail",
        "cloudtrail:StopLogging",
        "cloudtrail:UpdateTrail",
        "cloudtrail:PutEventSelectors",
        "cloudtrail:PutInsightSelectors",
        "config:DeleteConfigurationRecorder",
        "config:DeleteDeliveryChannel",
        "config:StopConfigurationRecorder",
        "config:PutConfigurationRecorder",
        "config:PutDeliveryChannel",
        "guardduty:DeleteDetector",
        "guardduty:UpdateDetector",
        "guardduty:DisassociateFromAdministratorAccount",
        "securityhub:DisableSecurityHub",
        "securityhub:DisassociateFromAdministratorAccount",
        "securityhub:BatchDisableStandards"
      ]
      }, length(var.protected_admin_role_patterns) == 0 ? {} : {
      Condition = { ArnNotLike = { "aws:PrincipalArn" = var.protected_admin_role_patterns } }
    })]
  })
}
