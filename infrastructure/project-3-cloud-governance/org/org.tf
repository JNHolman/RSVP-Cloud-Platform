# NOTE:
# In a real multi-account setup, this is where you'd use:
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
    "Resources": {
      "DummyWaitHandle": {
        "Type": "AWS::CloudFormation::WaitConditionHandle"
      }
    }
  }
  EOT

  tags = merge(
    var.tags,
    {
      Purpose = "Portfolio Organization Modeling"
    }
  )
}

output "org_stack_id" {
  value = aws_cloudformation_stack.org-documentation.id
}
