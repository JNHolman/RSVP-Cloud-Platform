######################################################
# ECS Fargate Service
######################################################

resource "aws_ecs_service" "app" {
  name            = "${var.project_name}-service"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.app.arn
  launch_type     = "FARGATE"
  desired_count   = 1

  network_configuration {
    subnets = [
      aws_subnet.public_a.id,
      aws_subnet.public_b.id,
    ]

    security_groups  = [aws_security_group.ecs_service.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.app.arn
    container_name   = "app"
    container_port   = 8080
  }

  depends_on = [
    aws_lb_listener.http,
  ]

  deployment_minimum_healthy_percent = 50
  deployment_maximum_percent         = 200

  tags = {
    Name        = "${var.project_name}-service"
    Project     = var.project_name
    Environment = "dev"
  }
}
