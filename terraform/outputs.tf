##############################################
#  Core Outputs – Easy to Test & Demo
##############################################

output "vpc_id" {
  description = "ID of the main VPC"
  value       = aws_vpc.main.id
}

output "public_subnets" {
  description = "IDs of the public subnets (ALB, NAT)"
  value       = aws_subnet.public[*].id
}

output "private_subnets" {
  description = "IDs of the private subnets (App, DB)"
  value       = aws_subnet.private[*].id
}

##############################################
#  Application Layer Outputs
##############################################

output "app_instance_ids" {
  description = "EC2 instance IDs for the RSVP app"
  value       = aws_instance.app[*].id
}

output "app_instance_private_ips" {
  description = "Private IPs of the RSVP app EC2 instances"
  value       = aws_instance.app[*].private_ip
}

##############################################
#  Load Balancer Outputs
##############################################

output "alb_dns_name" {
  description = "Public DNS name of the Application Load Balancer"
  value       = aws_lb.app_alb.dns_name
}
