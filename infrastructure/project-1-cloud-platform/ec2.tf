##############################################
#  AMI
##############################################

data "aws_ami" "amazon_linux" {
  most_recent = true

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  owners = ["137112412989"] # Amazon
}

##############################################
#  User Data – Apache + RSVP landing page
##############################################

locals {
  user_data = <<-EOF
#!/bin/bash
set -xe

yum update -y
yum install -y httpd

systemctl enable httpd
systemctl start httpd

HOSTNAME=$(hostname -f)

cat >/var/www/html/index.html <<HTML
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>RSVP Cloud Platform</title>
  <style>
    * { box-sizing: border-box; }
    body {
      margin: 0;
      padding: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
        sans-serif;
      background: #020617;
      color: #e5e7eb;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .card {
      background: #020617;
      border-radius: 20px;
      padding: 32px 40px;
      max-width: 840px;
      width: 90%;
      box-shadow:
        0 22px 45px rgba(15, 23, 42, 0.9),
        0 0 0 1px rgba(148, 163, 184, 0.1);
    }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 4px 14px;
      border-radius: 999px;
      background: #022c22;
      color: #bbf7d0;
      font-size: 12px;
      font-weight: 500;
      margin-bottom: 18px;
    }
    .badge-dot {
      width: 8px;
      height: 8px;
      border-radius: 999px;
      background: #22c55e;
      box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.25);
    }
    h1 {
      margin: 0 0 6px 0;
      font-size: 28px;
      letter-spacing: 0.03em;
    }
    .subtitle {
      margin: 0 0 28px 0;
      font-size: 14px;
      color: #9ca3af;
    }
    .layout {
      display: grid;
      grid-template-columns: 1.1fr 1.3fr;
      gap: 40px;
    }
    .section-title {
      font-size: 11px;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: #6b7280;
      margin-bottom: 8px;
    }
    .list { font-size: 13px; }
    .row {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      padding: 4px 0;
    }
    .label { color: #9ca3af; }
    .value {
      color: #e5e7eb;
      text-align: right;
      white-space: nowrap;
    }
    .section { margin-bottom: 18px; }
    .divider {
      height: 1px;
      background: radial-gradient(circle at center, #1e293b, transparent);
      margin: 18px 0 12px 0;
      opacity: 0.6;
    }
    .footer {
      font-size: 11px;
      color: #6b7280;
      margin-top: 10px;
      text-align: center;
    }
    .footer strong { color: #e5e7eb; }
    .value-highlight {
      color: #a855f7;
      font-weight: 500;
    }
    @media (max-width: 768px) {
      .layout { grid-template-columns: 1fr; gap: 24px; }
      .card { padding: 24px 18px; }
    }
  </style>
</head>
<body>
  <div class="card">
    <div class="badge">
      <span class="badge-dot"></span>
      <span>Deployed with Terraform by Josh</span>
    </div>

    <h1>RSVP Cloud Platform</h1>
    <p class="subtitle">
      Highly available, cost-optimized AWS stack for a small event-booking app.
    </p>

    <div class="layout">
      <div>
        <div class="section">
          <div class="section-title">Environment</div>
          <div class="list">
            <div class="row">
              <span class="label">Region</span>
              <span class="value">us-east-1</span>
            </div>
            <div class="row">
              <span class="label">VPC</span>
              <span class="value">Public + Private subnets, NAT, IGW</span>
            </div>
            <div class="row">
              <span class="label">Frontend access</span>
              <span class="value">Application Load Balancer (ALB)</span>
            </div>
          </div>
        </div>
      </div>

      <div>
        <div class="section">
          <div class="section-title">Workload</div>
          <div class="list">
            <div class="row">
              <span class="label">Compute</span>
              <span class="value">EC2 app servers in private subnets</span>
            </div>
            <div class="row">
              <span class="label">Database</span>
              <span class="value">Amazon RDS MySQL (dev-sized)</span>
            </div>
            <div class="row">
              <span class="label">Observability</span>
              <span class="value">CloudWatch metrics, alarms &amp; dashboard</span>
            </div>
            <div class="row">
              <span class="label">AI layer</span>
              <span class="value value-highlight">Log streams ready for AI summarization</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="divider"></div>
    <div class="footer">
      Instance: <strong>$HOSTNAME</strong>
    </div>
    <div class="footer" style="margin-top: 6px;">
      <a href="https://s3.console.aws.amazon.com/s3/buckets/rsvp-dev-ai-logs/summaries/"
         style="color:#a855f7; text-decoration:none; font-weight:500;"
         target="_blank">
         View AI summaries →
      </a>
    </div>
  </div>
</body>
</html>
HTML
EOF
}

##############################################
#  Launch Template
##############################################

resource "aws_launch_template" "app_lt" {
  name_prefix   = "${local.name_prefix}-lt-"
  image_id      = data.aws_ami.amazon_linux.id
  instance_type = var.instance_type

  iam_instance_profile {
    name = aws_iam_instance_profile.ec2_instance_profile.name
  }

  network_interfaces {
    security_groups = [aws_security_group.app_sg.id]
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
  name                      = "${local.name_prefix}-asg"
  max_size                  = 4
  min_size                  = 2
  desired_capacity          = 2
  health_check_type         = "EC2"
  health_check_grace_period = 120

  vpc_zone_identifier = aws_subnet.private[*].id

  launch_template {
    id      = aws_launch_template.app_lt.id
    version = "$Latest"
  }

  target_group_arns = [aws_lb_target_group.app_tg.arn]

  tag {
    key                 = "Name"
    value               = "${local.name_prefix}-app"
    propagate_at_launch = true
  }

  lifecycle {
    create_before_destroy = true
  }
}
