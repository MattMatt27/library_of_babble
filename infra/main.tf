# ============================================================================
# MAIN TERRAFORM CONFIGURATION FOR LIBRARY OF BABBLE
# ============================================================================
# This file orchestrates all AWS infrastructure needed to run the Flask app.
# It coordinates 6 modules: networking, security, database, IAM, ECR, and compute.
#
# SECRETS MANAGEMENT:
# All sensitive values (passwords, API keys) are stored in AWS Parameter Store
# and referenced here. ECS containers decrypt them at runtime. This keeps
# secrets out of version control and Terraform state files.
# ============================================================================

terraform {
  # Require Terraform version 1.5.0 or newer for modern features
  required_version = ">= 1.5.0"

  required_providers {
    # AWS provider version 5.x
    # ~> means "allow minor updates" (5.1, 5.2, etc.) but not major (6.0)
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Configure the AWS provider with region and default tags
provider "aws" {
  region = var.aws_region

  # Default tags are automatically applied to ALL resources created by Terraform
  # This makes it easy to identify what's part of this project in the AWS console
  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# ============================================================================
# DATA SOURCES - Fetch information from AWS
# ============================================================================
# These don't create anything; they just look up existing AWS information

# Get the current AWS account ID
# Used later for constructing IAM policy ARNs
data "aws_caller_identity" "current" {}

# Get list of available AWS availability zones in the current region
# Used to spread resources across multiple data centers for reliability
data "aws_availability_zones" "available" {
  state = "available"
}

# ============================================================================
# SECRETS FROM AWS PARAMETER STORE
# ============================================================================
# IMPORTANT: These secrets must be created MANUALLY in AWS Parameter Store
# BEFORE running Terraform. Use the AWS Console or CLI to create them.
#
# These data sources just look up the ARN (Amazon Resource Name) of each secret.
# The actual secret values are NOT stored in Terraform state for security.
# ECS containers will decrypt these at runtime using IAM permissions.
#
# with_decryption = false means "just give me the ARN, don't decrypt the value"
# This keeps sensitive values out of Terraform state files.
# ============================================================================

# Flask secret key - used for session encryption and CSRF protection
data "aws_ssm_parameter" "flask_secret_key" {
  name            = "/${var.project_name}/${var.environment}/flask-secret-key"
  with_decryption = false
}

# PostgreSQL database password for RDS instance creation
data "aws_ssm_parameter" "db_password" {
  name            = "/${var.project_name}/${var.environment}/db-password"
  with_decryption = false
}

# Full DATABASE_URL for the Flask app to connect to RDS
# Format: postgresql://username:password@host:port/database
# This is created AFTER RDS is deployed (see deployment guide)
data "aws_ssm_parameter" "database_url" {
  name            = "/${var.project_name}/${var.environment}/database-url"
  with_decryption = false
}

# Spotify API credentials - used for music/playlist features
data "aws_ssm_parameter" "spotify_client_id" {
  name            = "/${var.project_name}/${var.environment}/spotify-client-id"
  with_decryption = false
}

data "aws_ssm_parameter" "spotify_client_secret" {
  name            = "/${var.project_name}/${var.environment}/spotify-client-secret"
  with_decryption = false
}

data "aws_ssm_parameter" "spotify_username" {
  name            = "/${var.project_name}/${var.environment}/spotify-username"
  with_decryption = false
}

# TMDB (The Movie Database) API token - used for fetching movie/show data
data "aws_ssm_parameter" "tmdb_api_token" {
  name            = "/${var.project_name}/${var.environment}/tmdb-api-token"
  with_decryption = false
}

# Static storage URL - base URL for S3 image serving
data "aws_ssm_parameter" "static_storage_url" {
  name            = "/${var.project_name}/${var.environment}/static-storage-url"
  with_decryption = false
}

# S3 bucket name - for file uploads and storage operations
data "aws_ssm_parameter" "s3_bucket_name" {
  name            = "/${var.project_name}/${var.environment}/s3-bucket-name"
  with_decryption = false
}

# Cloudflare Tunnel token - authenticates the cloudflared sidecar with our tunnel
data "aws_ssm_parameter" "cloudflared_tunnel_token" {
  name            = "/${var.project_name}/${var.environment}/cloudflared-tunnel-token"
  with_decryption = false
}

# ============================================================================
# LOCAL VALUES - Computed values used throughout the configuration
# ============================================================================
# Locals are like variables but computed from other values
# They help avoid repeating the same expressions
locals {
  # Current AWS account ID - used for building IAM policy ARNs
  account_id  = data.aws_caller_identity.current.account_id

  # Prefix for naming all resources (e.g., "library-of-babble-prod")
  # This makes it easy to identify resources in AWS console
  name_prefix = "${var.project_name}-${var.environment}"

  # Map of all Parameter Store ARNs
  # These ARNs are passed to the IAM module to grant ECS permission to decrypt them
  # ECS containers will fetch and decrypt these at runtime using IAM roles
  parameter_arns = {
    flask_secret_key      = data.aws_ssm_parameter.flask_secret_key.arn
    db_password           = data.aws_ssm_parameter.db_password.arn
    database_url          = data.aws_ssm_parameter.database_url.arn
    spotify_client_id     = data.aws_ssm_parameter.spotify_client_id.arn
    spotify_client_secret = data.aws_ssm_parameter.spotify_client_secret.arn
    spotify_username      = data.aws_ssm_parameter.spotify_username.arn
    tmdb_api_token        = data.aws_ssm_parameter.tmdb_api_token.arn
    static_storage_url       = data.aws_ssm_parameter.static_storage_url.arn
    s3_bucket_name           = data.aws_ssm_parameter.s3_bucket_name.arn
    cloudflared_tunnel_token = data.aws_ssm_parameter.cloudflared_tunnel_token.arn
  }
}

# ============================================================================
# MODULE 1: NETWORKING
# ============================================================================
# Creates the VPC (Virtual Private Cloud) and subnets
# WHY: AWS resources need to live in a network. The VPC is like your own
# private data center in AWS. Subnets split it across availability zones
# for reliability (if one data center fails, the other keeps running).
module "networking" {
  source = "./modules/networking"

  name_prefix        = local.name_prefix
  vpc_cidr           = "10.0.0.0/16" # IP address range for the VPC
  availability_zones = slice(data.aws_availability_zones.available.names, 0, 2) # Use 2 AZs
}

# ============================================================================
# MODULE 2: SECURITY
# ============================================================================
# Creates Security Groups (firewall rules)
# WHY: Controls what network traffic is allowed in and out of resources.
# For example: allow HTTP/HTTPS traffic to ECS, only allow database access
# from the ECS containers, block everything else.
module "security" {
  source = "./modules/security"

  name_prefix = local.name_prefix
  vpc_id      = module.networking.vpc_id
}

# ============================================================================
# MODULE 3: DATABASE
# ============================================================================
# Creates the RDS PostgreSQL database instance
# WHY: Your Flask app needs a database to store books, movies, users, etc.
# RDS is AWS's managed database service - it handles backups, updates, and
# scaling automatically so you don't have to manage a database server yourself.
module "database" {
  source = "./modules/database"

  name_prefix           = local.name_prefix
  vpc_id                = module.networking.vpc_id
  db_subnet_group_name  = module.networking.db_subnet_group_name
  security_group_id     = module.security.db_security_group_id
  db_username           = var.db_username
  db_password_param_arn = data.aws_ssm_parameter.db_password.arn
  db_name               = replace(var.project_name, "-", "_") # library_of_babble (underscores not hyphens)
  instance_class        = var.db_instance_class # e.g., db.t3.micro
  allocated_storage     = var.db_allocated_storage # GB of storage
}

# ============================================================================
# MODULE 4: ECR (Elastic Container Registry)
# ============================================================================
# Creates a private Docker registry to store your Flask app images
# WHY: GitHub Actions pushes Docker images here, and ECS pulls from here.
# This is your private container registry (like Docker Hub, but AWS-hosted).
module "ecr" {
  source = "./modules/ecr"

  name_prefix = local.name_prefix
}

# ============================================================================
# MODULE 4b: S3 Storage (Static Assets)
# ============================================================================
# Creates an S3 bucket for static images and assets
# WHY: 5.7 GB of images is too large for Docker containers. S3 provides cheap,
# scalable storage. In production, STATIC_STORAGE_URL points to this bucket.
module "storage" {
  source = "./modules/storage"

  name_prefix = local.name_prefix
  aws_region  = var.aws_region
  bucket_name = "library-of-babble-static"  # Existing bucket with images
}

# ============================================================================
# MODULE 5: IAM (Identity and Access Management)
# ============================================================================
# Creates IAM roles that grant permissions to ECS containers
# WHY: ECS containers need permission to:
#   1. Pull Docker images from ECR (Elastic Container Registry)
#   2. Write logs to CloudWatch for debugging
#   3. Decrypt secrets from Parameter Store
#   4. Access S3 buckets for serving artwork and file assets
# Without these IAM roles, containers can't do any of the above.
module "iam" {
  source = "./modules/iam"

  name_prefix    = local.name_prefix
  account_id     = local.account_id
  aws_region     = var.aws_region
  parameter_arns = local.parameter_arns # Grant access to decrypt these secrets
}

# ============================================================================
# MODULE 6: COMPUTE (ECS Fargate)
# ============================================================================
# Creates the ECS cluster, task definition, and service to run your Flask app
# WHY: ECS Fargate runs Docker containers without managing servers. You just
# give it a Docker image and it handles running/scaling/restarting containers.
# This is the "brain" that actually runs your application code.
#
# COST NOTE: This is the main ongoing cost. Fargate charges per vCPU and GB
# of memory per hour. Using smaller task sizes (e.g., 0.25 vCPU, 512 MB RAM)
# keeps costs low for a portfolio site.
module "compute" {
  source = "./modules/compute"

  name_prefix             = local.name_prefix
  vpc_id                  = module.networking.vpc_id
  subnet_ids              = module.networking.public_subnet_ids # ECS tasks run in these subnets
  security_group_id       = module.security.ecs_security_group_id
  docker_image            = var.docker_image != "" ? var.docker_image : "${module.ecr.repository_url}:latest" # Use ECR if not specified
  task_execution_role_arn = module.iam.task_execution_role_arn # Permission to start containers
  task_role_arn           = module.iam.task_role_arn # Permission for running containers
  task_cpu                = var.ecs_task_cpu # e.g., "256" = 0.25 vCPU
  task_memory             = var.ecs_task_memory # e.g., "512" = 512 MB RAM
  desired_count           = var.ecs_desired_count # How many containers to run

  # Secret ARNs - ECS will fetch these at runtime
  flask_secret_key_arn      = data.aws_ssm_parameter.flask_secret_key.arn
  database_url_arn          = data.aws_ssm_parameter.database_url.arn
  spotify_client_id_arn     = data.aws_ssm_parameter.spotify_client_id.arn
  spotify_client_secret_arn = data.aws_ssm_parameter.spotify_client_secret.arn
  spotify_username_arn      = data.aws_ssm_parameter.spotify_username.arn
  tmdb_api_token_arn        = data.aws_ssm_parameter.tmdb_api_token.arn
  static_storage_url_arn       = data.aws_ssm_parameter.static_storage_url.arn
  s3_bucket_name_arn           = data.aws_ssm_parameter.s3_bucket_name.arn
  cloudflared_tunnel_token_arn = data.aws_ssm_parameter.cloudflared_tunnel_token.arn
}

# ============================================================================
# OUTPUTS - See outputs.tf for all output definitions
# ============================================================================
