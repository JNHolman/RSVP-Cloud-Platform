output "ecr_repository_urls" {
  description = "ECR repository URL by environment"
  value       = { for env, repo in aws_ecr_repository.app : env => repo.repository_url }
}

output "github_deploy_role_arns" {
  description = "GitHub Actions deployment role ARN by environment"
  value       = { for env, role in aws_iam_role.github_deploy : env => role.arn }
}

output "github_oidc_provider_arn" {
  value = aws_iam_openid_connect_provider.github_actions.arn
}
