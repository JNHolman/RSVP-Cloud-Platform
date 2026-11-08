# Project 2 — ECS & CI/CD

```text
GitHub Actions → tests/scans → ECR immutable image
                                  ↓
                          private ECS Fargate
                                  ↓
                          HTTPS health checks
```

GitHub Actions assumes short-lived AWS credentials through OIDC. Terraform owns the infrastructure and task-definition baseline; the deployment workflow owns application releases.

Two recovery paths are distinct: the **ECS circuit breaker** rolls back unhealthy task deployments, while **workflow rollback** handles failed release checks. The live exercise proved the native ECS rollback in **13m 47s**, not every workflow recovery path. Scaling configuration does not by itself prove load-driven scaling.

## Evidence checklist

[Exercise report and homepage screenshot](evidence/2026-11-08.md) · [Recorded observations](evidence/observations.json)

| Area | Evidence available | Evidence still needed |
|---|---|---|
| Delivery and networking | GitHub OIDC release, ECR digest, private targets and serving Git revision | Capture a release summary alongside the serving revision |
| Security and monitoring | WAF 403, CloudWatch streams and ECR scan comparison | Rebuild and rescan after a supported fix for the two remaining high findings |
| Recovery and scaling | ECS restored the previous healthy revision in 13m 47s | Exercise GitHub smoke-test rollback and measure scale-out and scale-in |

## Operations

Before using the production OIDC role, configure **GitHub Environment protection rules for `prod`**: **restrict deployment branches/tags** to approved release sources and require reviewer approval where supported. Environment protection is part of the **production authorization boundary**, because AWS trust scopes the OIDC subject to the repository and environment.


**Locations:** `project-2-ecs-cicd/bootstrap-delivery/` and `project-2-ecs-cicd/terraform/`

1. **Bootstrap delivery.** Use the bootstrap Terraform root in the intended AWS account. It manages the ECR repositories, the GitHub OIDC provider and environment-specific deployment roles. Confirm the account does not already have an independently owned OIDC provider before making changes.
2. **Configure GitHub.** Set `AWS_DEPLOY_ROLE_ARN` in the matching GitHub Environment. Also set `AWS_REGION` and `PROJECT_NAME` if not using the defaults (`us-east-1`, `rsvp-project2`). For stage/prod, restrict approved branches/tags and require approval where supported.
3. **Build the first image.** Run **ECS Project 2 - Bootstrap First Image** for the target environment. Copy the exact immutable Git-SHA image URI into the local runtime `terraform.tfvars` as `container_image`. Do not use `:latest`.
4. **Deploy the runtime.** Initialize `project-2-ecs-cicd/terraform/` with its matching dev backend, review its plan, and apply only after approval.
5. **Finish GitHub configuration.** Set `SERVICE_URL` to the service's verified HTTPS URL. Run **ECS Project 2 - Controlled Deploy**, then confirm that `/health` returns the expected release and environment.

**What to verify:** Two healthy private tasks in separate AZs, HTTPS, WAF, logs, the ECR image digest and GitHub's deployment result. The ECS circuit-breaker rollback and GitHub workflow rollback are separate behaviors. Verify each through its own controlled failure path. Use bounded load for autoscaling and record both scale-out and scale-in events.

**Task-definition ownership:** Terraform registers the infrastructure and security baseline, tagged `ConfigurationSource=TerraformBaseline`. The ECS service intentionally ignores `task_definition` drift so a later Terraform apply cannot roll back a GitHub-deployed application release. Therefore, after any Terraform change that modifies the ECS task definition, run **Controlled Deploy** before treating that configuration change as active. The workflow clones the latest Terraform baseline, replaces only the release image/version, and promotes that revision to the service.

[Platform overview](../README.md) · [Shared state, DNS, costs and teardown](../shared/OPERATIONS.md)
