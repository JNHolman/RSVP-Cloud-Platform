######################################################
# ECS Fargate Service — resilient production baseline
######################################################

resource "aws_ecs_service" "app" {
  name            = "${local.name_prefix}-service"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.app.arn
  launch_type     = "FARGATE"
  desired_count   = var.ecs_min_capacity

  platform_version = "LATEST"

  network_configuration {
    subnets = [
      aws_subnet.private_a.id,
      aws_subnet.private_b.id,
    ]

    security_groups  = [aws_security_group.ecs_service.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.app.arn
    container_name   = "app"
    container_port   = 8080
  }

  depends_on = [
    aws_lb_listener.https,
    aws_iam_role_policy_attachment.ecs_task_execution_policy,
  ]

  health_check_grace_period_seconds = 60

  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  enable_ecs_managed_tags = true
  propagate_tags          = "SERVICE"

  # Application releases are managed by the deployment workflow, which
  # registers immutable task-definition revisions. Prevent a later
  # infrastructure-only Terraform apply from rolling the service back
  # to the bootstrap task-definition revision.
  lifecycle {
    ignore_changes = [
      task_definition,
      desired_count,
    ]
  }

  tags = {
    Name        = "${local.name_prefix}-service"
    Project     = var.project_name
    Environment = var.environment
  }
}
