######################################################
# ECS Cluster
######################################################

resource "aws_ecs_cluster" "this" {
  name = "${var.project_name}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name        = "${var.project_name}-cluster"
    Project     = var.project_name
    Environment = "dev"
  }
}

######################################################
# ECS Task Definition (Fargate)
######################################################

resource "aws_ecs_task_definition" "app" {
  family                   = "${var.project_name}-task"
  cpu                      = "256"        # 0.25 vCPU
  memory                   = "512"        # 0.5 GB
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "app"
      image     = var.container_image
      essential = true

      portMappings = [
        {
          containerPort = 8080
          hostPort      = 8080
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "APP_VERSION"
          value = "v1.0.0"
        },
        {
          name  = "SERVICE_NAME"
          value = "RSVP Cloud Service"
        },
        {
          name  = "ENV_NAME"
          value = "dev"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.ecs_app.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])
}
