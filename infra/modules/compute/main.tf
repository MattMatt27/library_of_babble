# ============================================================================
# COMPUTE MODULE
# ============================================================================
# Creates ECS Fargate resources to run your Flask application in containers
#
# WHAT THIS MODULE CREATES:
# - ECS Cluster: Logical grouping of containers
# - Task Definition: Blueprint for running a container (Docker image, resources, env vars)
# - ECS Service: Ensures desired number of containers are always running
# - CloudWatch Log Group: Stores application logs for debugging
#
# WHY WE NEED THIS:
# This is the "brain" of your infrastructure - it actually runs your Flask app.
# ECS Fargate runs Docker containers without you managing servers. You just
# provide a Docker image and Fargate handles:
# - Starting containers
# - Restarting failed containers
# - Distributing containers across availability zones
# - Scaling containers up/down
#
# COST NOTE: This is your main ongoing cost
# - 0.25 vCPU (256 CPU units): ~$9/month
# - 512 MB memory: ~$2/month
# - Total: ~$11/month for 1 always-running container
# ============================================================================

# Input variables passed from main.tf
variable "name_prefix" {
  type        = string
  description = "Prefix for naming resources"
}

variable "vpc_id" {
  type        = string
  description = "VPC ID where ECS tasks will run"
}

variable "subnet_ids" {
  type        = list(string)
  description = "Subnet IDs where ECS tasks will run (public subnets)"
}

variable "security_group_id" {
  type        = string
  description = "Security group ID for ECS tasks"
}

variable "docker_image" {
  type        = string
  description = "Docker image to run (e.g., your-account.dkr.ecr.us-east-1.amazonaws.com/library-of-babble:latest)"
}

variable "task_execution_role_arn" {
  type        = string
  description = "IAM role ARN for ECS to start containers"
}

variable "task_role_arn" {
  type        = string
  description = "IAM role ARN for running application"
}

variable "task_cpu" {
  type        = number
  default     = 256
  description = "CPU units for container (256 = 0.25 vCPU)"
}

variable "task_memory" {
  type        = number
  default     = 512
  description = "Memory in MB for container"
}

variable "desired_count" {
  type        = number
  default     = 1
  description = "Number of containers to run"
}

# ========================================
# Secret ARNs (fetched from Parameter Store at container startup)
# ========================================
variable "flask_secret_key_arn" {
  type        = string
  description = "Parameter Store ARN for Flask secret key"
}

variable "database_url_arn" {
  type        = string
  description = "Parameter Store ARN for full DATABASE_URL connection string"
}

variable "spotify_client_id_arn" {
  type        = string
  description = "Parameter Store ARN for Spotify client ID"
}

variable "spotify_client_secret_arn" {
  type        = string
  description = "Parameter Store ARN for Spotify client secret"
}

variable "spotify_username_arn" {
  type        = string
  description = "Parameter Store ARN for Spotify username"
}

variable "tmdb_api_token_arn" {
  type        = string
  description = "Parameter Store ARN for TMDB API token"
}

variable "static_storage_url_arn" {
  type        = string
  description = "Parameter Store ARN for static storage base URL (S3)"
}

variable "s3_bucket_name_arn" {
  type        = string
  description = "Parameter Store ARN for S3 bucket name"
}

variable "cloudflared_tunnel_token_arn" {
  type        = string
  description = "Parameter Store ARN for the Cloudflare Tunnel token"
}


# ============================================================================
# CloudWatch Log Group
# ============================================================================
# Stores application logs from containers
# WHY: When your Flask app writes to stdout/stderr (like print statements or
# logging), those logs go to CloudWatch. This is essential for debugging
# errors and monitoring your app's behavior in production.
#
# COST NOTE: Minimal - first 5GB of logs per month are free, then $0.50/GB
resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/${var.name_prefix}"
  retention_in_days = 30 # Keep logs for 30 days, then auto-delete

  tags = {
    Name = "${var.name_prefix}-logs"
  }
}

# ============================================================================
# Data Source - Current AWS Region
# ============================================================================
# Used in the task definition for CloudWatch logs configuration
data "aws_region" "current" {}

# ============================================================================
# ECS Cluster
# ============================================================================
# Logical grouping of ECS services and tasks
# WHY: The cluster is just an organizational container - it doesn't cost
# anything by itself. It groups your services together for management.
resource "aws_ecs_cluster" "main" {
  name = "${var.name_prefix}-cluster"

  # Container Insights provides enhanced metrics and monitoring
  # WHY: Gives you CPU, memory, network metrics per container in CloudWatch
  # COST NOTE: Adds ~$1-2/month but very useful for debugging performance
  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = "${var.name_prefix}-cluster"
  }
}

# ============================================================================
# ECS Task Definition
# ============================================================================
# Blueprint for running your Flask application container
# WHY: This defines EVERYTHING about how your container runs:
# - Which Docker image to use
# - How much CPU and memory to allocate
# - What environment variables and secrets to inject
# - Where to send logs
# - How to check if the container is healthy
resource "aws_ecs_task_definition" "app" {
  family                   = "${var.name_prefix}-task"
  network_mode             = "awsvpc" # Required for Fargate
  requires_compatibilities = ["FARGATE"] # Use Fargate (serverless) not EC2
  cpu                      = var.task_cpu # e.g., 256 = 0.25 vCPU
  memory                   = var.task_memory # e.g., 512 = 512 MB RAM
  execution_role_arn       = var.task_execution_role_arn # Role for ECS to start container
  task_role_arn            = var.task_role_arn # Role for your app to use

  # ========================================
  # Container Configuration (JSON)
  # ========================================
  # This defines what runs inside the container
  container_definitions = jsonencode([
    {
      name  = "app"
      image = var.docker_image # Your Flask app Docker image from ECR

      # Expose port 5000 (Flask default)
      # WHY: Tells ECS that the container listens on port 5000
      portMappings = [
        {
          containerPort = 80
          protocol      = "tcp"
        }
      ]

      # ========================================
      # Environment Variables (Non-Sensitive)
      # ========================================
      # These are safe to store in plaintext - they're not secrets
      environment = [
        {
          name  = "FLASK_ENV"
          value = "production" # Disable Flask debug mode for security
        },
        {
          name  = "FLASK_DEBUG"
          value = "false" # Never enable debug in production!
        },
        {
          name  = "FLASK_HOST"
          value = "0.0.0.0" # Listen on all interfaces (required for container)
        },
        {
          name  = "FLASK_PORT"
          value = "80" # Port Flask listens on
        }
      ]

      # ========================================
      # Secrets (Sensitive Values from Parameter Store)
      # ========================================
      # ECS fetches these at container startup and injects as env vars
      # WHY: Keeps secrets out of Docker images and Terraform code
      # The difference from "environment": these are fetched from Parameter Store
      secrets = [
        {
          name      = "FLASK_SECRET_KEY"
          valueFrom = var.flask_secret_key_arn # Fetched from Parameter Store
        },
        {
          name      = "DATABASE_URL"
          valueFrom = var.database_url_arn # Full connection string from Parameter Store
        },
        {
          name      = "SPOTIPY_CLIENT_ID"
          valueFrom = var.spotify_client_id_arn
        },
        {
          name      = "SPOTIPY_CLIENT_SECRET"
          valueFrom = var.spotify_client_secret_arn
        },
        {
          name      = "SPOTIPY_USERNAME"
          valueFrom = var.spotify_username_arn
        },
        {
          name      = "TMDB_API_BEARER_TOKEN"
          valueFrom = var.tmdb_api_token_arn
        },
        {
          name      = "STATIC_STORAGE_URL"
          valueFrom = var.static_storage_url_arn
        },
        {
          name      = "S3_BUCKET_NAME"
          valueFrom = var.s3_bucket_name_arn
        }
      ]

      # ========================================
      # Logging Configuration
      # ========================================
      # Send container logs (stdout/stderr) to CloudWatch
      # WHY: Essential for debugging - you can view logs in AWS console
      logConfiguration = {
        logDriver = "awslogs" # Use AWS CloudWatch Logs
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.app.name
          "awslogs-region"        = data.aws_region.current.name
          "awslogs-stream-prefix" = "ecs"
        }
      }

      # ========================================
      # Health Check
      # ========================================
      # Periodically checks if the container is healthy
      # WHY: If health checks fail, ECS will stop and restart the container
      # This prevents serving traffic to broken containers
      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:80/ || exit 1"]
        interval    = 30 # Check every 30 seconds
        timeout     = 5 # Wait 5 seconds for response
        retries     = 3 # Fail after 3 consecutive failures
        startPeriod = 60 # Grace period at startup (60 seconds)
      }
    },
    # ========================================
    # Cloudflare Tunnel sidecar
    # ========================================
    # Runs cloudflared in the same task as the Flask app, sharing the network
    # namespace so it can reach the app at localhost:80. Connects outbound to
    # Cloudflare's edge — no public ingress needed.
    {
      name      = "cloudflared"
      image     = "cloudflare/cloudflared:2026.3.0"
      essential = true

      command = ["tunnel", "--no-autoupdate", "run"]

      secrets = [
        {
          name      = "TUNNEL_TOKEN"
          valueFrom = var.cloudflared_tunnel_token_arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.app.name
          "awslogs-region"        = data.aws_region.current.name
          "awslogs-stream-prefix" = "cloudflared"
        }
      }
    }
  ])

  tags = {
    Name = "${var.name_prefix}-task"
  }
}

# ============================================================================
# ECS Service
# ============================================================================
# Ensures your desired number of containers are always running
# WHY: The service is the "manager" that:
# - Starts containers based on the task definition
# - Restarts containers if they crash
# - Spreads containers across availability zones
# - Handles rolling updates when you deploy new code
resource "aws_ecs_service" "app" {
  name            = "${var.name_prefix}-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = var.desired_count # How many containers to keep running
  launch_type     = "FARGATE" # Use Fargate (serverless)

  # ========================================
  # Network Configuration
  # ========================================
  network_configuration {
    subnets          = var.subnet_ids # Public subnets from networking module
    security_groups  = [var.security_group_id] # Firewall rules from security module
    assign_public_ip = true # REQUIRED: Gives containers public IPs
    # WHY assign_public_ip = true: Without a NAT Gateway (which costs $32/month),
    # containers in public subnets need public IPs to access the internet
    # (for pulling Docker images, calling APIs, etc.)
  }

  # ========================================
  # Deployment Configuration
  # ========================================
  # Controls how updates are rolled out
  # deployment_maximum_percent = 200 means: during updates, ECS can temporarily
  # run 2x containers (e.g., 1 old + 1 new) to ensure zero downtime
  # deployment_minimum_healthy_percent = 100 means: always keep at least 100%
  # of desired containers healthy during updates
  deployment_maximum_percent         = 200
  deployment_minimum_healthy_percent = 100

  # ========================================
  # ECS Exec (Debugging)
  # ========================================
  # Allows you to SSH into running containers for debugging
  # WHY: Useful for troubleshooting issues in production
  # Run: aws ecs execute-command --cluster <cluster> --task <task-id> --command "/bin/bash" --interactive
  enable_execute_command = true

  tags = {
    Name = "${var.name_prefix}-service"
  }

  # ========================================
  # Lifecycle Configuration
  # ========================================
  # Prevents Terraform from reverting manual changes
  lifecycle {
    ignore_changes = [
      # Ignore task definition: You might update this via CI/CD pipelines
      # without running Terraform
      task_definition,
      # Ignore desired count: You might manually scale up/down for testing
      desired_count,
    ]
  }
}

# ============================================================================
# OUTPUTS - ECS resource details for reference
# ============================================================================
output "cluster_name" {
  description = "Name of the ECS cluster - useful for CLI commands"
  value       = aws_ecs_cluster.main.name
}

output "cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = aws_ecs_cluster.main.arn
}

output "service_name" {
  description = "Name of the ECS service - useful for CLI commands"
  value       = aws_ecs_service.app.name
}

output "task_definition_arn" {
  description = "ARN of the task definition - useful for deployments"
  value       = aws_ecs_task_definition.app.arn
}

output "log_group_name" {
  description = "Name of the CloudWatch log group - use to view logs in AWS console"
  value       = aws_cloudwatch_log_group.app.name
}
