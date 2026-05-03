# ============================================================================
# SECURITY MODULE
# ============================================================================
# Creates Security Groups (firewall rules) for ECS containers and RDS database
#
# WHAT THIS MODULE CREATES:
# - ECS Security Group: Controls traffic to/from ECS containers
# - RDS Security Group: Controls traffic to/from the database
#
# WHY WE NEED THIS:
# Security Groups act as virtual firewalls. They control what network traffic
# is allowed in (ingress) and out (egress) of resources. This module ensures:
# 1. Only CloudFlare can send HTTP/HTTPS traffic to ECS (adds DDoS protection)
# 2. Only ECS containers can connect to the database (prevents external access)
# 3. ECS can make outbound calls (to AWS services, Spotify API, etc.)
# ============================================================================

# Input variables passed from main.tf
variable "name_prefix" {
  type        = string
  description = "Prefix for naming resources"
}

variable "vpc_id" {
  type        = string
  description = "VPC ID where security groups will be created"
}

# ============================================================================
# ECS Security Group
# ============================================================================
# Firewall rules for ECS Fargate containers running the Flask app
# WHY: Controls what traffic can reach your application containers.
# No ingress rules — traffic arrives via the cloudflared sidecar's outbound
# tunnel to Cloudflare's edge, not via inbound public ports.
resource "aws_security_group" "ecs" {
  name        = "${var.name_prefix}-ecs-sg"
  description = "Security group for ECS Fargate tasks"
  vpc_id      = var.vpc_id

  # ========================================
  # EGRESS RULE: Allow all outbound traffic
  # ========================================
  # WHY: ECS containers need to make outbound connections to:
  # - Cloudflare's edge (cloudflared tunnel — IPs change frequently)
  # - AWS ECR / Parameter Store / S3 / CloudWatch (could pin to VPC endpoints
  #   at ~$7/mo each, currently not justified)
  # - Spotify / TMDB / Goodreads / Letterboxd (arbitrary public APIs)
  # tfsec:ignore:aws-ec2-no-public-egress-sgr — Open egress is required for
  #   the cloudflared tunnel and external APIs; tightening would need an
  #   egress proxy or ~$30/mo of VPC endpoints. Defense lives at the
  #   application layer (no inbound, IAM, secrets in SSM).
  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1" # -1 means all protocols
    cidr_blocks = ["0.0.0.0/0"] # All internet destinations
  }

  tags = {
    Name = "${var.name_prefix}-ecs-sg"
  }
}

# ============================================================================
# RDS Security Group
# ============================================================================
# Firewall rules for the RDS PostgreSQL database
# WHY: Ensures the database is ONLY accessible from ECS containers, never
# from the internet. This is critical for security.
resource "aws_security_group" "rds" {
  name        = "${var.name_prefix}-rds-sg"
  description = "Security group for RDS PostgreSQL database"
  vpc_id      = var.vpc_id

  # ========================================
  # INGRESS RULE: PostgreSQL from ECS only
  # ========================================
  # Allow port 5432 (PostgreSQL) ONLY from the ECS security group
  # WHY: This means only ECS containers can connect to the database.
  # No one from the internet, no one from other AWS resources - only ECS.
  # This is the most secure database configuration.
  ingress {
    description     = "PostgreSQL from ECS tasks"
    from_port       = 5432 # PostgreSQL default port
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id] # Only from ECS security group
  }

  # ========================================
  # EGRESS RULE: Allow all outbound
  # ========================================
  # WHY: RDS doesn't typically make outbound connections, but AWS requires
  # an egress rule. This allows RDS to communicate with AWS services for
  # management, updates, and backups if needed.
  # tfsec:ignore:aws-ec2-no-public-egress-sgr — RDS does not initiate outbound
  #   traffic in normal operation; this rule is essentially inert.
  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.name_prefix}-rds-sg"
  }
}

# ============================================================================
# OUTPUTS - Security Group IDs exported to other modules
# ============================================================================
output "ecs_security_group_id" {
  description = "Security group ID for ECS tasks - passed to compute module"
  value       = aws_security_group.ecs.id
}

output "db_security_group_id" {
  description = "Security group ID for RDS database - passed to database module"
  value       = aws_security_group.rds.id
}
