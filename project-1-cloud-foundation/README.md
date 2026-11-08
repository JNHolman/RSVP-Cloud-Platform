# Part 1 — Cloud Foundation

**A traditional AWS application architecture, built to test how networking, security, monitoring, and recovery work together.**

This is where the platform's engineering principles began. A public application needs to accept requests, but that doesn't mean its servers or database belong on the public internet. I designed the traffic path around an HTTPS load balancer, private compute across two Availability Zones, and a private encrypted database.

```text
Client → HTTPS / WAF / ALB → private EC2 targets (AZ A and AZ B)
                                      |
                           Intended private RDS tier
```

The application-to-database path is represented in Terraform, but the original live test served a separate demo page and validated RDS recovery independently.

## The engineering work

**Networking and availability.** The VPC separates public entry points from private application subnets. Security-group rules limit access from the ALB to application instances and from the application tier to the database. Each Availability Zone has its own NAT gateway for private outbound access, avoiding a single-AZ egress dependency. An Auto Scaling Group places instances behind the load balancer.

**Monitoring and security.** WAF filters requests at the edge. VPC Flow Logs, application logs, and CloudWatch alarms provide visibility into traffic, failed requests, and unhealthy targets. An EventBridge-to-Lambda incident-analysis path is defined to examine bounded logs and metrics; results are advisory and stored in encrypted S3 and DynamoDB, with a deterministic fallback.

**Database recovery.** RDS uses encrypted storage, managed credentials, and snapshot/backup configuration. The RDS encryption key has a Terraform destruction guard because retaining a snapshot without its decryption key is not meaningful recovery. My live recovery test used a native RDS snapshot and a separate restored database.

The trade-off is cost. These controls are useful for an enterprise workload, but running compute, a Multi-AZ database, and network egress infrastructure continuously would have been excessive for RSVP Society's intermittent events.

## What the AWS exercise actually proved

![Live foundation application page](evidence/live-homepage.png)

On November 8, 2026, the test environment had two healthy private EC2 targets in different Availability Zones. HTTPS served the demo page, WAF rejected a synthetic malicious request, logs arrived, and an unhealthy-target alarm entered and exited ALARM.

For recovery, I wrote a known database record, created an encrypted snapshot, restored it to a separate private RDS instance, and read the same record over TLS. **Measured restore: 10 minutes 2 seconds.**

One incident-analysis Lambda invocation initially failed on DynamoDB key access. After restricting the required decrypt permission to the demo encryption key and context, a direct retry stored a fallback result. A separate local handler test exercised a live AI response.

**The limits:** the demo page did not query RDS; alarm-to-Lambda delivery was not verified; and this exercise did not measure point-in-time recovery or AZ failover. Those distinctions matter when evaluating the architecture.

[Full dated test record](evidence/2026-11-08.md) · [Captured observations](evidence/observations.json)

This established the network boundaries, failure visibility, and recovery discipline carried into Part 2.

[Platform overview](../README.md) · [Part 2: ECS & CI/CD](../project-2-ecs-cicd/README.md)
