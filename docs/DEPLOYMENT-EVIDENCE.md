# Deployment Evidence Plan

The goal is to prove the important engineering claims with a small number of high-value screenshots and command outputs. Avoid turning the repository into an AWS console screenshot dump.

## 1. CI quality gate

Capture one successful GitHub Actions run showing the required quality jobs pass:

- Terraform formatting/init/validation
- TFLint
- Checkov
- Python lint/tests
- dependency audit
- Docker build
- Trivy image scan

**Evidence:** one workflow summary screenshot plus the workflow URL/commit SHA.

## 2. Network and edge security

Prove:

- ALB is internet-facing
- workloads use private subnets
- ECS tasks have no public IP
- HTTPS listener/certificate is active
- HTTP redirects to HTTPS
- WAF is associated with the public edge

**Evidence:** one VPC/subnet view, one ECS network view, one ALB/WAF view.

## 3. ECS resilience and deployment

Prove:

- two or more healthy tasks across Availability Zones
- autoscaling target exists
- deployment circuit breaker is enabled
- running image uses the Git SHA
- `/health` succeeds over HTTPS

Then deliberately deploy a safe broken revision and capture the failed deployment and rollback to the previous task definition.

**Evidence:** service health screenshot, task definition/image SHA screenshot, workflow rollback output.

## 4. RDS data protection

Prove:

- private database
- Multi-AZ enabled
- encrypted storage
- managed secret
- backups/PITR enabled
- deletion protection enabled

Perform a controlled restore into a new temporary database and record:

- restore start
- restore available time
- application/database validation result
- cleanup time

**Evidence:** RDS configuration screenshot plus recovery exercise record.

## 5. Observability

Trigger or safely simulate at least one alarm condition.

Prove:

- CloudWatch dashboard
- alarm transition
- SNS/EventBridge path
- operational notification

**Evidence:** dashboard screenshot and alarm history.

## 6. Governance

When the multi-account layer is deployed, prove:

- Organizations OU layout
- SCP attachment
- delegated Security administrator
- organization CloudTrail
- centralized Config aggregation
- Identity Center permission sets

**Evidence:** one organization tree screenshot and one centralized-security screenshot. Do not expose sensitive account identifiers unnecessarily.

## 7. API security

Prove:

- Cognito-protected API route rejects unauthenticated requests
- authenticated request succeeds
- WAF is associated
- API throttling/logging is enabled

**Evidence:** two request results plus API/WAF configuration screenshot.

## 8. AI-assisted operations

Generate one real operational signal and capture:

- source telemetry/finding
- AI summary
- evidence referenced
- confidence
- recommended next checks

For FinOps, capture a real Cost Explorer-backed report. Do not use synthetic spend data.

**Evidence:** one incident-analysis record and one FinOps record.

## 9. Recovery result

After the ECS rollback and RDS restore exercises, record actual measured recovery data.

Do not change documentation from **RTO/RPO target** to **achieved** until the exercise supports the claim.

## Suggested public evidence set

Aim for approximately 8–12 polished images total:

1. architecture overview
2. successful CI run
3. private multi-AZ network/workload placement
4. ECS healthy service + immutable image
5. deployment rollback
6. RDS protection settings
7. CloudWatch operations dashboard
8. Organizations/security overview
9. API authentication/WAF
10. AI incident analysis
11. RDS restore result

The evidence should prove the story, not repeat every AWS console page.
