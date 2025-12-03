##############################################
# AMI lookup for Amazon Linux 2
##############################################

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

##############################################
# Security Group for App EC2 instances
##############################################

resource "aws_security_group" "app_sg" {
  name        = "${var.project_name}-${var.environment}-app-sg"
  description = "Allow HTTP to app instances and outbound internet"
  vpc_id      = aws_vpc.main.id

  # HTTP from anywhere (demo-friendly)
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Outbound anywhere
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-app-sg"
    Project     = var.project_name
    Environment = var.environment
  }
}

##############################################
# App EC2 instances (behind the ALB)
##############################################

resource "aws_instance" "app" {
  count = 2

  ami           = data.aws_ami.amazon_linux.id
  instance_type = var.app_instance_type

  # Use public subnets so we can test easily
  subnet_id = element(aws_subnet.public[*].id, count.index)

  vpc_security_group_ids      = [aws_security_group.app_sg.id]
  associate_public_ip_address = true

  # Simple, boring, RELIABLE user_data
  user_data = <<-EOF
    #!/bin/bash
    yum update -y
    yum install -y httpd -y

    systemctl enable httpd
    systemctl start httpd

    cat > /var/www/html/index.html <<'HTML'
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <title>RSVP Cloud Platform</title>
      <style>
        body {
          margin: 0;
          padding: 0;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
          background: #020617;
          color: #e5e7eb;
          display: flex;
          justify-content: center;
          align-items: center;
          min-height: 100vh;
        }
        .card {
          background: radial-gradient(circle at top left, #0f172a, #020617);
          border-radius: 24px;
          padding: 40px 56px;
          box-shadow: 0 24px 80px rgba(15, 23, 42, 0.9);
          width: 900px;
          max-width: 95vw;
        }
        .badge {
          display: inline-block;
          padding: 6px 16px;
          border-radius: 999px;
          background: rgba(34, 197, 94, 0.1);
          color: #22c55e;
          font-size: 12px;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          margin-bottom: 18px;
        }
        h1 {
          margin: 0;
          font-size: 32px;
          letter-spacing: 0.03em;
        }
        .subtitle {
          margin-top: 8px;
          margin-bottom: 28px;
          color: #9ca3af;
          font-size: 14px;
        }
        .grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 24px 64px;
          font-size: 13px;
        }
        .section-title {
          color: #6b7280;
          text-transform: uppercase;
          letter-spacing: 0.18em;
          font-size: 11px;
          margin-bottom: 10px;
        }
        .row {
          display: flex;
          justify-content: space-between;
          margin-bottom: 4px;
        }
        .label {
          color: #9ca3af;
        }
        .value {
          color: #e5e7eb;
          font-weight: 500;
        }
        .value-strong {
          color: #e5e7eb;
          font-weight: 600;
        }
        .ai {
          color: #a855f7;
        }
        .footer {
          margin-top: 32px;
          font-size: 12px;
          color: #6b7280;
          text-align: center;
        }
      </style>
    </head>
    <body>
      <div class="card">
        <div class="badge">Deployed with Terraform by Josh</div>
        <h1>RSVP Cloud Platform</h1>
        <div class="subtitle">
          Highly available, cost-optimized AWS stack for a small event-booking app.
        </div>

        <div class="grid">
          <div>
            <div class="section-title">Environment</div>
            <div class="row">
              <div class="label">Region</div>
              <div class="value">us-east-1</div>
            </div>
            <div class="row">
              <div class="label">VPC</div>
              <div class="value">Public + Private subnets, NAT, IGW</div>
            </div>
            <div class="row">
              <div class="label">Frontend access</div>
              <div class="value-strong">Application Load Balancer (ALB)</div>
            </div>
          </div>

          <div>
            <div class="section-title">Workload</div>
            <div class="row">
              <div class="label">Compute</div>
              <div class="value">EC2 app servers in private subnets</div>
            </div>
            <div class="row">
              <div class="label">Database</div>
              <div class="value">Amazon RDS (single-AZ dev)</div>
            </div>
            <div class="row">
              <div class="label">Observability</div>
              <div class="value">CloudWatch metrics, alarms &amp; dashboard</div>
            </div>
            <div class="row">
              <div class="label ai">AI layer</div>
              <div class="value ai">Log streams ready for AI summarization</div>
            </div>
          </div>
        </div>

        <div class="footer">
          Instance: HOST_PLACEHOLDER
        </div>
      </div>
    </body>
    </html>
    HTML

    # Replace placeholder with the real hostname
    sed -i "s/HOST_PLACEHOLDER/$(hostname -f)/g" /var/www/html/index.html
  EOF





  tags = {
    Name        = "${var.project_name}-${var.environment}-app-${count.index}"
    Project     = var.project_name
    Environment = var.environment
    Role        = "app"
  }
}


