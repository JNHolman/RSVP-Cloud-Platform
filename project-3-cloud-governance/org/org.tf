# NOTE:
# In a real multi-account setup, this is where you’d use:
#   aws_organizations_organization
#   aws_organizations_policy (SCPs)
#   aws_organizations_account
#
# For the lab / portfolio, we MODEL the org via tags + naming and
# explain the real-world mapping in the README.

resource "aws_cloudformation_stack" "org-documentation" {
  name          = "${var.project_name}-org-metadata"
  template_body = <<-EOT
  {
    "AWSTemplateFormatVersion": "2010-09-09",
    "Description": "Metadata-only stack used as a placeholder for AWS Organization modeling for portfolio purposes.",
    "Resources": {}
  }
  EOT

  tags = merge(
    var.tags,
    {
      "Component"        = "org"
      "ManagementLabel"  = var.account_labels.management
      "SecurityLabel"    = var.account_labels.security
      "LoggingLabel"     = var.account_labels.logging
      "WorkloadLabel"    = var.account_labels.workload
    }
  )
}
