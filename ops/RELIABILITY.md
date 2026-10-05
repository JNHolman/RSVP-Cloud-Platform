# Reliability and Recovery Objectives

This portfolio treats recoverability as an engineering requirement, not just a backup setting.

| Capability | Target | Control |
|---|---:|---|
| ECS application availability | Multi-AZ, minimum 2 healthy tasks | ECS service + ALB health checks + autoscaling + deployment rollback |
| Application RTO | <= 15 minutes for failed application deployment | ECS deployment circuit breaker and previous-task-definition rollback |
| Database RPO | <= 24 hours from AWS Backup, typically <= 5 minutes from RDS PITR | RDS automated backups/PITR + independent AWS Backup recovery points |
| Database RTO | <= 60 minutes for restore exercise | Documented snapshot/PITR restore runbook and validation script |
| Detection | <= 5 minutes for sustained service/database degradation | CloudWatch alarms + SNS |

These are lab SLO targets and must be validated by timed recovery exercises before being represented as achieved production SLOs.
