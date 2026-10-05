# Project 2 Delivery Bootstrap

This stack is applied once per AWS account before the ECS runtime stack.

It creates:

- one GitHub Actions OIDC provider for the AWS account
- immutable ECR repositories for dev, stage, and prod
- one environment-scoped GitHub deployment role per environment

The deployment roles are restricted to the repository and matching GitHub Environment. ECR push access is repository-specific, and `iam:PassRole` is restricted to the deterministic ECS execution/task role names for that environment.

## Bootstrap order

1. Apply this stack.
2. Save `github_deploy_role_arns` into the matching GitHub Environment variable `AWS_DEPLOY_ROLE_ARN`.
3. If you override Terraform `aws_region` or `project_name`, set matching GitHub Environment variables `AWS_REGION` and `PROJECT_NAME`. When omitted, the workflows use the Terraform defaults (`us-east-1` and `rsvp-project2`).
4. Run `.github/workflows/ecs-project2-bootstrap-image.yml` to push the first SHA-pinned image.
5. Use that image URI as `container_image` when applying the ECS runtime stack.
6. Use the normal controlled deployment workflow for subsequent releases.
