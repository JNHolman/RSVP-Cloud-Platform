##############################################
#  AMI
##############################################

data "aws_ssm_parameter" "amazon_linux_2023_ami" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

##############################################
#  User Data – Apache + RSVP landing page + /health
##############################################

locals {
  user_data = <<-EOF2
#!/bin/bash
set -xe

dnf install -y httpd amazon-cloudwatch-agent

systemctl enable httpd
systemctl start httpd

HOSTNAME=$(hostname -f)

cat >/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json <<CWA
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/httpd/access_log",
            "log_group_name": "/${local.name_prefix}/app",
            "log_stream_name": "{instance_id}/access"
          },
          {
            "file_path": "/var/log/httpd/error_log",
            "log_group_name": "/${local.name_prefix}/app",
            "log_stream_name": "{instance_id}/error"
          }
        ]
      }
    }
  }
}
CWA
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json \
  -s

cat >/var/www/html/index.html <<HTML
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>RSVP Cloud Platform</title>
</head>
<body>
  <h1>RSVP Cloud Platform</h1>
  <p>Private application tier behind an HTTPS Application Load Balancer.</p>
  <p>Instance: $HOSTNAME</p>
</body>
</html>
HTML

echo "ok" > /var/www/html/health
chmod 644 /var/www/html/health
EOF2
}

##############################################
#  Launch Template
##############################################

resource "aws_launch_template" "app_lt" {
  name_prefix   = "${local.name_prefix}-lt-"
  image_id      = data.aws_ssm_parameter.amazon_linux_2023_ami.value
  instance_type = var.instance_type

  iam_instance_profile {
    name = aws_iam_instance_profile.ec2_instance_profile.name
  }

  network_interfaces {
    security_groups             = [aws_security_group.app_sg.id]
    associate_public_ip_address = false
  }

  # Require IMDSv2 so instance-role credentials cannot be fetched through
  # unauthenticated metadata requests.
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  # The ASG CPU alarm evaluates at 60-second periods. EC2 CPU metrics are
  # five-minute by default, so enable detailed monitoring for one-minute data.
  monitoring {
    enabled = true
  }

  # Make root-volume encryption explicit instead of depending on account defaults.
  block_device_mappings {
    device_name = "/dev/xvda"

    ebs {
      encrypted             = true
      volume_type           = "gp3"
      delete_on_termination = true
    }
  }

  user_data = base64encode(local.user_data)

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "${local.name_prefix}-app"
      Environment = var.environment
      Project     = var.project_name
    }
  }
}

##############################################
#  Auto Scaling Group
##############################################

resource "aws_autoscaling_group" "app_asg" {
  # create_before_destroy requires a unique replacement name. A fixed `name`
  # can deadlock replacement because AWS will reject the duplicate ASG name.
  name_prefix               = "${local.name_prefix}-asg-"
  max_size                  = 4
  min_size                  = 2
  desired_capacity          = 2
  health_check_type         = "ELB"
  health_check_grace_period = 180
  vpc_zone_identifier       = aws_subnet.private[*].id

  launch_template {
    id      = aws_launch_template.app_lt.id
    version = aws_launch_template.app_lt.latest_version
  }

  target_group_arns = [aws_lb_target_group.app_tg.arn]

  # The instance profile can exist before its managed-policy attachments have
  # propagated. Do not launch first-boot instances until SSM and CloudWatch
  # Agent permissions are actually attached to the role.
  depends_on = [
    aws_iam_role_policy_attachment.ec2_basic_ssm,
    aws_iam_role_policy_attachment.ec2_cloudwatch_logs,
  ]

  instance_refresh {
    strategy = "Rolling"

    preferences {
      min_healthy_percentage = 100
      instance_warmup        = 180
    }

    triggers = ["launch_template"]
  }

  tag {
    key                 = "Name"
    value               = "${local.name_prefix}-app"
    propagate_at_launch = true
  }

  lifecycle {
    create_before_destroy = true
  }
}


##############################################
#  Auto Scaling policy
##############################################

resource "aws_autoscaling_policy" "app_cpu_target" {
  name                   = "${local.name_prefix}-cpu-target"
  autoscaling_group_name = aws_autoscaling_group.app_asg.name
  policy_type            = "TargetTrackingScaling"
  estimated_instance_warmup = 180

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }

    target_value = var.asg_cpu_target
  }
}
