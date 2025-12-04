# VPC resources for ECS Project 2 will go here
######################################################
# Data: Availability Zones
######################################################

data "aws_availability_zones" "available" {
  state = "available"
}

######################################################
# VPC
######################################################

resource "aws_vpc" "this" {
  cidr_block           = "10.20.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name        = "${var.project_name}-vpc"
    Project     = var.project_name
    Environment = "dev"
  }
}

######################################################
# Public Subnets (for ALB, NAT if needed)
######################################################

resource "aws_subnet" "public_a" {
  vpc_id                  = aws_vpc.this.id
  cidr_block              = "10.20.1.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = {
    Name        = "${var.project_name}-public-a"
    Project     = var.project_name
    Environment = "dev"
    Tier        = "public"
  }
}

resource "aws_subnet" "public_b" {
  vpc_id                  = aws_vpc.this.id
  cidr_block              = "10.20.2.0/24"
  availability_zone       = data.aws_availability_zones.available.names[1]
  map_public_ip_on_launch = true

  tags = {
    Name        = "${var.project_name}-public-b"
    Project     = var.project_name
    Environment = "dev"
    Tier        = "public"
  }
}

######################################################
# Private Subnets (for ECS Fargate tasks)
######################################################

resource "aws_subnet" "private_a" {
  vpc_id            = aws_vpc.this.id
  cidr_block        = "10.20.11.0/24"
  availability_zone = data.aws_availability_zones.available.names[0]

  tags = {
    Name        = "${var.project_name}-private-a"
    Project     = var.project_name
    Environment = "dev"
    Tier        = "private"
  }
}

resource "aws_subnet" "private_b" {
  vpc_id            = aws_vpc.this.id
  cidr_block        = "10.20.12.0/24"
  availability_zone = data.aws_availability_zones.available.names[1]

  tags = {
    Name        = "${var.project_name}-private-b"
    Project     = var.project_name
    Environment = "dev"
    Tier        = "private"
  }
}

######################################################
# Internet Gateway + Public Route Table
######################################################

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = {
    Name        = "${var.project_name}-igw"
    Project     = var.project_name
    Environment = "dev"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.this.id
  }

  tags = {
    Name        = "${var.project_name}-public-rt"
    Project     = var.project_name
    Environment = "dev"
  }
}

resource "aws_route_table_association" "public_a" {
  subnet_id      = aws_subnet.public_a.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_b" {
  subnet_id      = aws_subnet.public_b.id
  route_table_id = aws_route_table.public.id
}
