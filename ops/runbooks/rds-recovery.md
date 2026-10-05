# Runbook: RDS Recovery

## Trigger
- Database unavailable
- Data corruption or operator error
- RDS storage/CPU alarm with confirmed service impact

## Recovery decision
1. Infrastructure/AZ failure: rely on Multi-AZ failover first.
2. Logical/data corruption: restore to a new DB instance using point-in-time recovery.
3. Backup-system exercise: restore the latest AWS Backup recovery point to a new DB instance.

Never restore over the production database. Restore to a new identifier, validate data/application connectivity, then perform a controlled cutover.

## Validation
- Confirm automated-backup retention and latest restorable time.
- Confirm an AWS Backup recovery point exists in the recovery vault.
- Restore to a non-production identifier.
- Validate engine status, encryption, security groups, TLS, and expected application data.
- Record start/end timestamps and measured RTO/RPO.
- Delete the temporary restored DB after evidence is captured.
