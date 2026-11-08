output "organization_id" {
  value = aws_organizations_organization.this.id
}

output "organization_root_id" {
  value = aws_organizations_organization.this.roots[0].id
}

output "account_ids" {
  description = "Account IDs consumed by the delegated admin and workload stacks."
  value       = local.account_ids
}

output "ou_ids" {
  value = {
    security       = aws_organizations_organizational_unit.security.id
    infrastructure = aws_organizations_organizational_unit.infrastructure.id
    workloads      = aws_organizations_organizational_unit.workloads.id
    nonprod        = aws_organizations_organizational_unit.nonprod.id
    prod           = aws_organizations_organizational_unit.prod.id
  }
}
