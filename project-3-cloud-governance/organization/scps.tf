module "scp_policies" {
  source                        = "../modules/scp-policies"
  protected_admin_role_patterns = var.protected_admin_role_patterns
}

resource "aws_organizations_policy" "deny_leave_org" {
  name        = "${var.project_name}-deny-leave-organization"
  description = "Prevents member accounts from leaving the AWS Organization."
  type        = "SERVICE_CONTROL_POLICY"
  content     = module.scp_policies.deny_leave_org
}

# Attach at the organization root so every member account inherits the guardrail,
# including Security, Log Archive, Shared Services, NonProd, and Prod. SCPs do
# not restrict the Organizations management account.
resource "aws_organizations_policy_attachment" "deny_leave_root" {
  policy_id = aws_organizations_policy.deny_leave_org.id
  target_id = aws_organizations_organization.this.roots[0].id
}

resource "aws_organizations_policy" "protect_security_controls" {
  name        = "${var.project_name}-protect-security-controls"
  description = "Prevents ordinary workload principals from disabling centralized logging and security controls."
  type        = "SERVICE_CONTROL_POLICY"
  content     = module.scp_policies.protect_security_controls
}

resource "aws_organizations_policy_attachment" "protect_nonprod" {
  policy_id = aws_organizations_policy.protect_security_controls.id
  target_id = aws_organizations_organizational_unit.nonprod.id
}

resource "aws_organizations_policy_attachment" "protect_prod" {
  policy_id = aws_organizations_policy.protect_security_controls.id
  target_id = aws_organizations_organizational_unit.prod.id
}
