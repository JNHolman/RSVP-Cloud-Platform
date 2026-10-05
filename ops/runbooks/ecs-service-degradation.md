# Runbook: ECS Service Degradation

## Trigger
- ECS CPU/memory alarm
- ALB target 5XX alarm
- Unhealthy target alarm
- Failed deployment or failed HTTPS health check

## Triage
1. Check the CloudWatch operations dashboard.
2. Inspect ECS service events and deployment state.
3. Compare desired, running, and pending task counts.
4. Inspect stopped-task reasons and application CloudWatch logs.
5. Confirm ALB target health and `/health` response.

## Recovery
- Failed release: allow the deployment circuit breaker or CI workflow to restore the previous task definition.
- Capacity pressure: confirm Application Auto Scaling is adding tasks; raise max capacity only after identifying the bottleneck.
- Single unhealthy task: allow ECS to replace it; investigate the stopped task before forcing another deployment.

## Exit criteria
- Running task count equals desired count.
- At least two healthy targets across availability zones.
- `/health` returns HTTP 200 over HTTPS.
- 5XX and unhealthy-target alarms return to OK.
