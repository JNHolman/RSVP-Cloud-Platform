run "default_denies" {
  command = plan
  assert {
    condition = alltrue([for policy in [output.deny_leave_org, output.protect_security_controls] :
      jsondecode(policy).Statement[0].Effect == "Deny" &&
      jsondecode(policy).Statement[0].Resource == "*" &&
      !can(jsondecode(policy).Statement[0].Condition)
    ])
    error_message = "Default denies must cover all resources without exceptions."
  }
  assert {
    condition = alltrue([for action in [
      "cloudtrail:StopLogging", "config:StopConfigurationRecorder",
      "guardduty:DeleteDetector", "securityhub:DisableSecurityHub"
    ] : contains(jsondecode(output.protect_security_controls).Statement[0].Action, action)])
    error_message = "The rendered security policy must deny disabling each central control."
  }
  assert {
    condition     = contains(jsondecode(output.deny_leave_org).Statement[0].Action, "organizations:LeaveOrganization") && contains(jsondecode(output.deny_leave_org).Statement[0].Action, "account:CloseAccount")
    error_message = "Organization membership and account closure must be protected."
  }
}
run "explicit_admin" {
  command = plan
  variables {
    protected_admin_role_patterns = ["arn:aws:iam::111111111111:role/SecurityAdmin"]
  }
  assert {
    condition     = tolist(jsondecode(output.protect_security_controls).Statement[0].Condition.ArnNotLike["aws:PrincipalArn"]) == var.protected_admin_role_patterns && !can(jsondecode(output.deny_leave_org).Statement[0].Condition)
    error_message = "Only the named role may bypass the security-control deny."
  }
}
run "reject_wildcard" {
  command = plan
  variables {
    protected_admin_role_patterns = ["arn:aws:iam::111111111111:role/Admin?"]
  }
  expect_failures = [var.protected_admin_role_patterns]
}
