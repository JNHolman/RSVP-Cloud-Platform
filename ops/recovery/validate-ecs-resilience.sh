#!/usr/bin/env bash
set -euo pipefail
: "${ECS_CLUSTER:?Set ECS_CLUSTER}"
: "${ECS_SERVICE:?Set ECS_SERVICE}"
AWS_REGION="${AWS_REGION:-us-east-1}"

aws ecs describe-services --region "$AWS_REGION" --cluster "$ECS_CLUSTER" --services "$ECS_SERVICE" \
  --query 'services[0].{Status:status,Desired:desiredCount,Running:runningCount,Pending:pendingCount,Deployments:deployments[].{Status:status,Rollout:rolloutState,Desired:desiredCount,Running:runningCount,Failed:failedTasks}}'
