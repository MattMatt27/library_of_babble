# ============================================================================
# NETWORKING MODULE
# ============================================================================
# Creates the Virtual Private Cloud (VPC) and all networking components
#
# WHAT THIS MODULE CREATES:
# - VPC: Your private network in AWS
# - Public subnets: Where ECS containers run (need internet access)
# - Private subnets: Where the RDS database lives (no direct internet access)
# - Internet Gateway: Allows resources to communicate with the internet
# - Route tables: Direct network traffic appropriately
#
# WHY WE NEED THIS:
# AWS requires all resources to live in a VPC. We split the VPC into public
# and private subnets for security: ECS containers need internet access to
# serve web traffic, but the database should be isolated in private subnets.
# ============================================================================

# Input variables passed from main.tf
variable "name_prefix" {
  type        = string
  description = "Prefix for naming resources (e.g., library-of-babble-prod)"
}

variable "vpc_cidr" {
  type        = string
  description = "IP address range for the VPC (e.g., 10.0.0.0/16)"
}

variable "availability_zones" {
  type        = list(string)
  description = "List of AWS availability zones to use (for high availability)"
}

# ============================================================================
# VPC (Virtual Private Cloud)
# ============================================================================
# Creates your own isolated network in AWS
# WHY: All AWS resources must live in a VPC - it's like your own private
# data center with configurable IP addressing and routing
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr # e.g., 10.0.0.0/16 (65,536 IP addresses)
  enable_dns_hostnames = true # Allows resources to get DNS names
  enable_dns_support   = true # Enables DNS resolution within the VPC

  tags = {
    Name = "${var.name_prefix}-vpc"
  }
}

# ============================================================================
# Internet Gateway
# ============================================================================
# Allows resources in public subnets to communicate with the internet
# WHY: Without this, ECS containers couldn't receive web traffic or make
# outbound API calls (to Spotify, TMDB, etc.)
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.name_prefix}-igw"
  }
}

# ============================================================================
# Public Subnets
# ============================================================================
# Subnets where ECS containers run - they get public IP addresses
# WHY: ECS containers need public IPs to receive HTTP/HTTPS traffic from users
# and to make outbound API calls. Using multiple AZs means if one data center
# fails, the other keeps running.
#
# CIDR CALCULATION: cidrsubnet(10.0.0.0/16, 8, 0) = 10.0.0.0/24 (256 IPs)
#                   cidrsubnet(10.0.0.0/16, 8, 1) = 10.0.1.0/24 (256 IPs)
resource "aws_subnet" "public" {
  count                   = length(var.availability_zones) # Create one per AZ
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true # Auto-assign public IPs to resources

  tags = {
    Name = "${var.name_prefix}-public-${var.availability_zones[count.index]}"
    Type = "public"
  }
}

# ============================================================================
# Private Subnets
# ============================================================================
# Subnets where the RDS database lives - NO public IP addresses
# WHY: Databases should never be directly accessible from the internet for
# security. Only ECS containers in the VPC can connect to the database.
# RDS requires subnets in at least 2 AZs for high availability.
#
# CIDR CALCULATION: cidrsubnet(10.0.0.0/16, 8, 10) = 10.0.10.0/24
#                   cidrsubnet(10.0.0.0/16, 8, 11) = 10.0.11.0/24
# (Using +10 offset to avoid overlapping with public subnets)
resource "aws_subnet" "private" {
  count             = length(var.availability_zones) # Create one per AZ
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 10)
  availability_zone = var.availability_zones[count.index]

  tags = {
    Name = "${var.name_prefix}-private-${var.availability_zones[count.index]}"
    Type = "private"
  }
}

# ============================================================================
# Public Route Table
# ============================================================================
# Defines how traffic flows from public subnets
# WHY: The route table tells AWS "send all internet-bound traffic (0.0.0.0/0)
# to the Internet Gateway". Without this route, public subnets wouldn't
# actually be able to reach the internet.
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0" # All internet traffic
    gateway_id = aws_internet_gateway.main.id # Send it through the IGW
  }

  tags = {
    Name = "${var.name_prefix}-public-rt"
  }
}

# ============================================================================
# Route Table Associations
# ============================================================================
# Links public subnets to the public route table
# WHY: Subnets don't automatically use a route table - you must explicitly
# associate them. This tells each public subnet to use the public route table.
resource "aws_route_table_association" "public" {
  count          = length(var.availability_zones)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# ============================================================================
# Database Subnet Group
# ============================================================================
# Groups private subnets together for RDS to use
# WHY: RDS requires you to specify subnets in at least 2 availability zones
# for high availability. If one AZ fails, RDS can failover to the other.
# This resource bundles the private subnets together for RDS to use.
resource "aws_db_subnet_group" "main" {
  name       = "${var.name_prefix}-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id # All private subnet IDs

  tags = {
    Name = "${var.name_prefix}-db-subnet-group"
  }
}

# ============================================================================
# OUTPUTS - Values exported to main.tf and other modules
# ============================================================================
# These values are passed to other modules (security, database, compute)
# so they can reference the networking resources created here
output "vpc_id" {
  description = "VPC ID - used by security groups and other resources"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "Public subnet IDs - where ECS tasks will run"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "Private subnet IDs - where RDS database will run"
  value       = aws_subnet.private[*].id
}

output "db_subnet_group_name" {
  description = "DB subnet group name - passed to RDS module"
  value       = aws_db_subnet_group.main.name
}
