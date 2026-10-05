# Architecture and Design Decisions

## Architecture objective

The platform is designed around one principle: **the application is only one part of the system**. Deployment, security, observability, governance, and recovery are part of the architecture as well.

## Logical layers

### Edge

- DNS
- AWS WAF
- HTTPS Application Load Balancer
- ACM certificate

The edge is public. Application compute is not.

### Workload

- EC2 Auto Scaling for the infrastructure-focused implementation
- ECS Fargate for the container-delivery implementation
- private subnets across Availability Zones
- autoscaling and health checks

### Data

- private RDS MySQL
- Multi-AZ
- KMS encryption
- Secrets Manager-managed credentials
- PITR and AWS Backup

### Delivery

- GitHub Actions
- OIDC federation to AWS
- immutable Git SHA images
- CI quality/security gates
- controlled environment deployment
- health validation and rollback

### Governance

- AWS Organizations
- OUs and SCPs
- delegated security administration
- dedicated log-archive pattern
- organization CloudTrail and Config aggregation
- IAM Identity Center

### Operations

- CloudWatch metrics/logs/dashboards/alarms
- SNS and EventBridge
- recovery runbooks and validation scripts
- AI-assisted SRE/security/FinOps analysis

## Trust boundaries

1. Internet traffic terminates at managed public edge services.
2. Application compute is private and accepts only expected load-balancer traffic.
3. The database accepts traffic only from the application security boundary.
4. GitHub can assume only the intended deployment role through OIDC.
5. Workload accounts are separated from security and logging administration.
6. AI roles can read bounded evidence and write analysis outputs but cannot perform infrastructure remediation.

## Deployment boundaries

The governance layer uses multiple Terraform roots intentionally. Organization bootstrap, log archive, audit trail, delegated security, and Identity Center operate under different AWS trust/account contexts. Treating them as one root would hide the actual operational boundaries and make account bootstrap less safe.

## Production vs portfolio operation

The production design favors resilience and security. A portfolio deployment can be short-lived to control AWS spend, but the source architecture does not weaken production controls simply to make the diagram cheaper.
