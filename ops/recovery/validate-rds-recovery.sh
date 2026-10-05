#!/usr/bin/env bash
set -euo pipefail
: "${DB_IDENTIFIER:?Set DB_IDENTIFIER}"
: "${BACKUP_VAULT:?Set BACKUP_VAULT}"
AWS_REGION="${AWS_REGION:-us-east-1}"

aws rds describe-db-instances --region "$AWS_REGION" --db-instance-identifier "$DB_IDENTIFIER" \
  --query 'DBInstances[0].{Status:DBInstanceStatus,MultiAZ:MultiAZ,Encrypted:StorageEncrypted,Retention:BackupRetentionPeriod,EarliestRestore:EarliestRestorableTime,LatestRestore:LatestRestorableTime,DeletionProtection:DeletionProtection}'

aws backup list-recovery-points-by-backup-vault --region "$AWS_REGION" --backup-vault-name "$BACKUP_VAULT" \
  --query 'sort_by(RecoveryPoints,&CreationDate)[-5:].{Created:CreationDate,Status:Status,ResourceArn:ResourceArn}' --output json
