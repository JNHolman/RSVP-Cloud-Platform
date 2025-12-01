##############################################
#  EC2 Application Layer
##############################################

# Find a recent Amazon Linux 2 AMI for this region
data "aws_ami" "amazon_linux_2" {
  most_recent = true

  owners = ["amazon"]

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
#  Security Group for App Instances
##############################################

resource "aws_security_group" "app_sg" {
  name        = "${var.project_name}-${var.environment}-app-sg"
  description = "Security group for RSVP application instances"
  vpc_id      = aws_vpc.main.id

  # Inbound HTTP (will later be tightened to ALB-only, but for demo keep simple)
  ingress {
    description = "HTTP from load balancer / public"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow outbound to anywhere (for OS updates, talking to RDS, etc.)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-app-sg"
    Environment = var.environment
    Project     = var.project_name
    Tier        = "app"
  }
}

##############################################
#  User data – simple web app placeholder
##############################################

locals {
  app_user_data = <<-EOF
    #!/bin/bash
    yum update -y
    yum install -y nginx
    systemctl enable nginx
    cat << 'HTML' > /usr/share/nginx/html/index.html
    <html>
      <head>
        <title>RSVP Cloud Platform</title>
      </head>
      <body>
        <h1>RSVP Cloud Platform</h1>
        <p>Highly available, cost-optimized AWS platform for a small event-booking app.</p>
      </body>
    </html>
    HTML
    systemctl start nginx
  EOF
}

##############################################
#  EC2 Instances (App Tier)
##############################################

resource "aws_instance" "app" {
  count                       = 2
  ami                         = data.aws_ami.amazon_linux_2.id
  instance_type               = var.instance_type
  subnet_id                   = aws_subnet.private[count.index].id
  associate_public_ip_address = false

  vpc_security_group_ids = [aws_security_group.app_sg.id]

  user_data = local.app_user_data

  tags = {
    Name        = "${var.project_name}-${var.environment}-app-${count.index + 1}"
    Environment = var.environment
    Project     = var.project_name
    Tier        = "app"
  }
}
