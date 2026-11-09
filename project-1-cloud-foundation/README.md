# Project 1 — Cloud Foundation

An HTTPS request crosses a protected public edge to a private application tier. When a health alarm changes state, the platform gathers evidence and sends an advisory report to the operator.

```mermaid
flowchart TB
  client["Browser"] -->|HTTPS| edge["Application Load Balancer · ACM + AWS WAF"]
  subgraph vpc["Foundation VPC · us-east-1"]
    edge --> asg["Private EC2 Auto Scaling group · two Availability Zones"]
    asg -->|IAM reader · MySQL over TLS| db[("Encrypted Multi-AZ RDS")]
  end
  db --> backup["Native snapshots · PITR · AWS Backup"]
  asg -->|Application logs| logs["CloudWatch Logs"]
  edge -->|Target health and 5xx metrics| alarm["CloudWatch alarms"]
  classDef data fill:#eaf3fb,stroke:#376b98,color:#102c42
  classDef ops fill:#e9f5ef,stroke:#35815a,color:#133d28
  class db,backup data
  class alarm,logs ops
```

**Recovery benchmark:** the historical encrypted snapshot restore recovered a known database row in **10m 02s**. [Timestamped recovery timeline](evidence/2026-11-08.md#recovery-timeline)

## Live integration on November 8

The shared Flask application read an operator-inserted marker from private MySQL through the EC2 role and a TLS-verified IAM connection. Both HTTPS endpoints later returned the same three records. The EC2 screenshot captures the first two, before the recovery checkpoint marker was added. [Live foundation page](evidence/live-rds-reader.png)

On the first rollout, Gunicorn failed before startup because systemd could not open its stderr file. Correcting the log path restored the service. The real load-balancer metrics capture the target-health transitions.

![CloudWatch load balancer target health during the EC2 rollout](evidence/live-target-health.png)

### AI incident analysis

An operator set the CloudWatch alarm `rsvp-pf1-dev-target-5xx-high` to **ALARM**. From there the investigation ran automatically.

| Step | What happened in AWS |
|---|---|
| Trigger | EventBridge routed the alarm change to the incident Lambda. |
| Investigation | Lambda collected **77 log entries**. OpenAI returned an advisory analysis. |
| Report | The pipeline saved the report in KMS-encrypted S3 storage and recorded the incident in DynamoDB. |
| Notification | SNS delivered the notification to an encrypted SQS test subscriber. Human email delivery remains unverified. |

#### From the saved AI report

At 23:24:01 UTC on November 8 the analyst recorded the following excerpts from the 77-entry investigation. All six excerpts below were checked against the original report in encrypted S3 storage. The repository contains the excerpts and execution record. An authorized reader with the full report can verify its SHA-256 digest: `53a5efd6d23b93dc24a7db25169caeaeee13ddf34e2dd8b924af2da3b8bfd69f`.

**Observed in the logs** (report field `evidence_used`):

> At 23:18:59, /health returned 503 to ELB-HealthChecker/2.0.
>
> Additional /health 503 responses occurred at 23:19:29 and 23:19:32.

**Model assessment** (from `summary` and `likely_root_cause`):

> Health checks recovered to HTTP 200 by 23:19:59 and remained healthy through the end of the supplied logs, including after later Gunicorn/Apache startup messages.
>
> Separately, the observed earlier 503s were likely caused by Apache proxy failures to connect to the local backend service on 127.0.0.1:8080, consistent with the backend not listening or restarting at that time. The supplied evidence does not prove why the backend was unavailable.

**Recommended checks** (from `recommended_checks`):

> Confirm in CloudWatch alarm history whether the ALARM transition was operator-set rather than metric-driven.
>
> Verify current /health, /api/reservations, and target group status remain healthy before closing the incident.

The operator had set the alarm to exercise the notification path. The earlier 503s were real observations within the collected window. Restarting the service, changing configuration and closing the incident remained operator decisions.

## Recovery evidence

AWS Backup completed a separate restore in 16m 48s. A later private TLS read confirmed the expected row. RDS also reported a Multi-AZ failover start and completion 19.85 seconds apart.

The point-in-time recovery readback records a TLS query against the private, encrypted restored database. The expected rehearsal row was readable 13m 50s after the restore request.

[Earlier networking, WAF and recovery exercise](evidence/2026-11-08.md)

The alarm handler bounds and redacts its log sample before requesting analysis. The Terraform configuration defines the access path and database recovery settings. [Investigation handler](terraform/ai_log_summarizer.py) · [Network boundaries](terraform/vpc.tf) · [Database configuration](terraform/rds.tf)

<details><summary>Technical evidence records</summary>

[Incident delivery](evidence/live-incident.json) · [Recovery observations](evidence/live-recovery.json) · [Point-in-time readback](evidence/live-pitr.json)

</details>
