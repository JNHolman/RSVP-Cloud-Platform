data "aws_iam_policy_document" "deny_leave_org" {
  statement {
    sid    = "DenyLeavingOrganizationAndClosingAccount"
    effect = "Deny"
    actions = [
      "organizations:LeaveOrganization",
      "account:CloseAccount",
    ]
    resources = ["*"]
  }
}

resource "aws_organizations_policy" "deny_leave_org" {
  name        = "${var.project_name}-deny-leave-organization"
  description = "Prevents member accounts from leaving the AWS Organization."
  type        = "SERVICE_CONTROL_POLICY"
  content     = data.aws_iam_policy_document.deny_leave_org.json
}

# Attach at the organization root so every member account inherits the guardrail,
# including Security, Log Archive, Shared Services, NonProd, and Prod. SCPs do
# not restrict the Organizations management account.
resource "aws_organizations_policy_attachment" "deny_leave_root" {
  policy_id = aws_organizations_policy.deny_leave_org.id
  target_id = aws_organizations_organization.this.roots[0].id
}

data "aws_iam_policy_document" "protect_security_controls" {
  statement {
    sid    = "ProtectCentralSecurityControls"
    effect = "Deny"
    actions = [
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
    resources = ["*"]

    dynamic "condition" {
      for_each = length(var.protected_admin_role_patterns) > 0 ? [1] : []
      content {
        test     = "ArnNotLike"
        variable = "aws:PrincipalArn"
        values   = var.protected_admin_role_patterns
      }
    }
  }
}

resource "aws_organizations_policy" "protect_security_controls" {
  name        = "${var.project_name}-protect-security-controls"
  description = "Prevents ordinary workload principals from disabling centralized logging and security controls."
  type        = "SERVICE_CONTROL_POLICY"
  content     = data.aws_iam_policy_document.protect_security_controls.json
}

resource "aws_organizations_policy_attachment" "protect_nonprod" {
  policy_id = aws_organizations_policy.protect_security_controls.id
  target_id = aws_organizations_organizational_unit.nonprod.id
}

resource "aws_organizations_policy_attachment" "protect_prod" {
  policy_id = aws_organizations_policy.protect_security_controls.id
  target_id = aws_organizations_organizational_unit.prod.id
}
