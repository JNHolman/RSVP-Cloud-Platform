# Part 2 — ECS & CI/CD

**Private containers, traceable releases, and a measured recovery from a failed deployment.**

A healthy server is not enough if the release pipeline can quietly replace it with the wrong image. I built a GitHub Actions delivery path for a private ECS Fargate service, with tests, vulnerability scanning, immutable Git-SHA image tags, and a health check that returns the serving version.

```text
GitHub Actions → tests / scan → temporary AWS role (OIDC)
                                    |
                          ECR image → ECS release

Client traffic → HTTPS / WAF / ALB → private ECS tasks (two AZs)
```

## How the release design works

**Authenticate without stored access keys.** GitHub Actions uses OpenID Connect (OIDC) to obtain a temporary AWS role scoped to the repository and a named GitHub Environment. The delivery bootstrap defines those roles and ECR resources. For production, the GitHub Environment also needs appropriate approval and release-branch protections.

[OIDC trust and ECR bootstrap](bootstrap-delivery/main.tf) · [Release workflow](../.github/workflows/ecs-project2-deploy.yml)

**Keep deployments traceable.** The image is tied to a Git commit, and the workflow checks both the HTTPS health response and the expected version. Two private Fargate tasks sit behind an HTTPS ALB and WAF, using the same basic boundary as the EC2 foundation.

**Prevent conflicting changes.** Terraform registers the tagged task-definition baseline and manages the service infrastructure; GitHub Actions creates and promotes application revisions. The ECS service ignores task-definition drift so an infrastructure-only Terraform apply cannot unintentionally roll a release backward. A changed baseline must be picked up through the release process.

[Service ownership and rollback settings](terraform/ecs_service.tf) · [Application source](app/app.py)

**Handle failures at the right layer.** ECS has a deployment circuit breaker for unhealthy tasks. The workflow separately rolls back on deployment or smoke-test failure. I treated them as distinct mechanisms rather than claiming that testing one proved the other.

## What happened in the AWS exercise

The first container wouldn't start because Gunicorn needed to write worker heartbeat files and the container root filesystem was read-only. Using `/dev/shm` for those files solved the startup problem without loosening the filesystem restriction.

On November 8, 2026, GitHub Actions authenticated through OIDC and delivered an immutable image. Two private ECS tasks became healthy across AZs, with the expected digest and serving Git revision. HTTPS, WAF rejection, and application logs were observed.

I deliberately registered an ECS revision with a failing startup command. The native circuit breaker returned the service to the previous healthy revision in **13 minutes 47 seconds** without a manual service update. A post-demo base-image update reduced ECR HIGH findings from nine to two; the remaining findings were not declared resolved.

**Not proven in that exercise:** workflow smoke-failure rollback, load-driven scaling, or stage/prod deployment. Those are different claims from the native circuit-breaker test.

[Release and recovery timeline](evidence/2026-11-08.md) · [ECR scan comparison](evidence/image-rescan.json) · [Successful GitHub Actions deployment](https://github.com/JNHolman/RSVP-Cloud-Platform/actions/runs/42458363871)

Part 2 applies the same security and recovery standards to changes in application software. Part 3 extends that thinking to account-level controls.

[Platform overview](../README.md) · [Part 3: Cloud Governance](../project-3-cloud-governance/README.md)
