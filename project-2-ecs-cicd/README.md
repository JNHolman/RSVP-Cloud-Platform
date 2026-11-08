# Part 2 — ECS & CI/CD

**The same emphasis on private networking and recovery, applied to shipping application changes.**

Hosting a workload safely is only half the problem. Releases introduce new failure modes: bad images, unhealthy containers, unexpected configuration changes, and uncertainty about which version is running. I used ECS Fargate and GitHub Actions to make those changes traceable and recoverable.

```text
GitHub Actions → tests / scan → OIDC role → ECR image tagged with Git SHA
                                              |
                                    private ECS Fargate
                                              |
                                    HTTPS / WAF / ALB
```

## The engineering work

**Scoped release credentials.** GitHub Actions uses OIDC to assume a temporary AWS role rather than storing long-lived deployment keys. The trust is restricted by repository and GitHub Environment; production access depends on the appropriate environment and branch protections.

**Knowing exactly what shipped.** Images are identified by Git commit rather than a mutable `latest` tag. The workflow verifies the expected version through the live health endpoint and confirms the release against the task definition and image.

**Separate ownership for separate changes.** Terraform owns the ECS infrastructure and tagged task-definition baseline. GitHub Actions owns application revision updates. The service ignores Terraform's task-definition drift so an infrastructure-only apply cannot quietly roll a release back. When the baseline changes, the release workflow must pick up that configuration explicitly.

**Recovery without manual guesswork.** ECS can revert an unhealthy deployment through its circuit breaker. The GitHub workflow has a different rollback path for failed deployment or smoke checks. Those protections overlap in purpose but are not the same test.

## What the AWS exercise actually proved

![Live ECS application page displaying its Git revision](evidence/live-homepage.png)

On November 8, 2026, GitHub Actions used OIDC to deploy an immutable image. Two ECS tasks were healthy in private subnets across two Availability Zones. HTTPS, WAF rejection, CloudWatch logging, and the running image digest were verified.

The first container launch failed because Gunicorn couldn't write its worker temporary file on a read-only root filesystem. Moving the worker heartbeat location to `/dev/shm` solved the startup problem while preserving the filesystem restriction.

I also introduced a deliberately broken ECS revision. The circuit breaker restored the previous healthy version in **13 minutes 47 seconds**, without a manual service update. After the demo, an updated base image reduced HIGH ECR scan findings from **nine to two**; the remaining findings were not represented as fixed.

**The limits:** the live failure test proved native ECS rollback, not the separate workflow smoke-test rollback. Autoscaling was configured but not load-tested, and stage/prod deployment was not demonstrated.

[Original release and rollback record](evidence/2026-11-08.md) · [Image scan comparison](evidence/image-rescan.json) · [Controlled deploy workflow run](https://github.com/JNHolman/RSVP-Cloud-Platform/actions/runs/42458363871)

This layer extends the foundation's security and reliability decisions into how software gets delivered. Part 3 considers how an organization would govern those decisions across accounts.

[Platform overview](../README.md) · [Part 3: Cloud Governance](../project-3-cloud-governance/README.md)
