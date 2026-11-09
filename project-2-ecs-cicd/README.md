# Project 2 — ECS & CI/CD

A healthy container can still serve the wrong software. I used two independent checks in the dev release. ECS monitored task health. GitHub Actions checked the version that clients actually received over HTTPS.

The release used GitHub OIDC for temporary AWS credentials. The build published an immutable Git-SHA image to ECR, with Trivy and ECR scan results available for review. Two private Fargate tasks in separate Availability Zones ran the recorded image digest. The application read the same three rows as the EC2 service through VPC peering, using an IAM database token and verified TLS. [Build run](https://github.com/JNHolman/RSVP-Cloud-Platform/actions/runs/42534475017) · [Successful release](https://github.com/JNHolman/RSVP-Cloud-Platform/actions/runs/42535097319) · [Task digests and database readback](evidence/live-release-recovery.json) · [Serving application](evidence/live-rds-reader.png)

## Live integrated release on November 8

| GitHub Actions step | Recorded result | Why it matters |
|---|---|---|
| Smoke test · 23:34:10 UTC | “Unexpected release health, version or environment” | The candidate answered health requests but served the deliberately incorrect version. |
| Roll back failed deployment · 23:37:34 UTC | “Previous release verified after rollback” | The workflow restored revision 6 and verified the prior serving version, `43ef326`, in **3m 23s**. |

The failed status on [the workflow run](https://github.com/JNHolman/RSVP-Cloud-Platform/actions/runs/42535446228) records the rejected candidate. In a separate exercise an unhealthy revision failed inside ECS itself. Its deployment circuit breaker recovered the previous release in **13m 47s**. [Circuit-breaker timeline and security scan findings](evidence/2026-11-08.md)

![ECS desired and running task counts sampled during the exercise](evidence/scale-out.svg)

The test used a temporary 10% CPU target. Desired capacity rose first, then a third task reached running state. Observation ended before scale-in was confirmed. [Timestamped task counts](evidence/live-scaling.json)

**Task-definition ownership.** Terraform tagged the infrastructure baseline `ConfigurationSource=TerraformBaseline`. The release workflow cloned it and selected the image. That separation explains why, after any Terraform change that modifies the ECS task definition, operators run **Controlled Deploy** to promote the updated baseline. GitHub Environment protection rules for `prod` restrict deployment branches/tags and form part of the production authorization boundary. The exercises used dev.
