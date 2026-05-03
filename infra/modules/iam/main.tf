# ============================================================================
# IAM MODULE
# ============================================================================
# Creates IAM roles and policies that grant permissions to ECS containers
#
# WHAT THIS MODULE CREATES:
# - Task Execution Role: Used BY ECS to start containers (pull images, get secrets)
# - Task Role: Used BY YOUR APPLICATION running inside containers
# - Policies: Define what each role is allowed to do
#
# WHY WE NEED THIS:
# In AWS, everything works on the principle of least privilege. By default,
# nothing has permission to do anything. IAM roles explicitly grant permissions.
# Without these roles:
# - ECS couldn't pull your Docker image from ECR
# - Containers couldn't decrypt secrets from Parameter Store
# - Your app couldn't write logs to CloudWatch
# - Your app couldn't access S3 for artwork/files
#
# TWO ROLES EXPLAINED:
# 1. Task Execution Role: What ECS needs to START the container
# 2. Task Role: What YOUR APP needs WHILE RUNNING
# ============================================================================

# Input variables passed from main.tf
variable "name_prefix" {
  type        = string
  description = "Prefix for naming resources"
}

variable "account_id" {
  type        = string
  description = "AWS account ID for constructing ARNs"
}

variable "aws_region" {
  type        = string
  description = "AWS region for KMS key references"
}

variable "parameter_arns" {
  description = "Map of Parameter Store ARNs that ECS needs access to"
  type        = map(string)
}

# ============================================================================
# TASK EXECUTION ROLE
# ============================================================================
# Used BY ECS to start and manage containers
# WHY: ECS needs permission to:
# 1. Pull Docker images from ECR (Elastic Container Registry)
# 2. Write container logs to CloudWatch Logs
# 3. Fetch secrets from Parameter Store (added below)
resource "aws_iam_role" "task_execution" {
  name = "${var.name_prefix}-ecs-task-execution-role"

  # Trust policy: Allows ECS service to assume this role
  # "AssumeRole" means "ECS can temporarily use these permissions"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com" # Only ECS can use this role
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name = "${var.name_prefix}-ecs-task-execution-role"
  }
}

# ============================================================================
# Attach AWS Managed Policy
# ============================================================================
# AWS provides a pre-built policy with standard ECS permissions
# WHY: This gives ECS permission to pull images from ECR and write to CloudWatch
# It's easier and more maintainable than writing these permissions from scratch
resource "aws_iam_role_policy_attachment" "task_execution_policy" {
  role       = aws_iam_role.task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ============================================================================
# Parameter Store Access Policy
# ============================================================================
# Allows ECS to decrypt and fetch secrets from Parameter Store
# WHY: ECS needs to fetch secrets (DB password, API keys, etc.) at container
# startup time. This policy grants permission to read those specific parameters.
resource "aws_iam_role_policy" "parameter_store_access" {
  name = "${var.name_prefix}-parameter-store-access"
  role = aws_iam_role.task_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # ========================================
      # Permission 1: Read Parameters
      # ========================================
      # Allows reading specific parameters from Parameter Store
      # WHY: ECS needs to fetch flask-secret-key, db-password, spotify-*, tmdb-*
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameters",    # Get multiple parameters at once
          "ssm:GetParameter",     # Get a single parameter
          "ssm:GetParametersByPath" # Get all parameters under a path
        ]
        Resource = [
          for arn in values(var.parameter_arns) : arn # Only these specific parameters
        ]
      },
      # ========================================
      # Permission 2: Decrypt with KMS
      # ========================================
      # Allows decrypting secrets encrypted with AWS KMS
      # WHY: Parameter Store uses KMS to encrypt secrets. ECS needs permission
      # to decrypt them. The condition ensures this only works via Parameter Store.
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt" # Decrypt encrypted values
        ]
        Resource = "arn:aws:kms:${var.aws_region}:${var.account_id}:key/*"
        Condition = {
          StringEquals = {
            # Only allow decryption when called through Parameter Store
            # (prevents direct KMS access)
            "kms:ViaService" = "ssm.${var.aws_region}.amazonaws.com"
          }
        }
      }
    ]
  })
}

# ============================================================================
# TASK ROLE
# ============================================================================
# Used BY YOUR APPLICATION running inside the container
# WHY: This is for permissions your Flask app needs while running:
# - Accessing S3 to serve artwork and file assets
# - Any other AWS services your app uses
#
# IMPORTANT DISTINCTION:
# - Task Execution Role: What ECS needs to START the container
# - Task Role: What YOUR CODE needs WHILE RUNNING
resource "aws_iam_role" "task" {
  name = "${var.name_prefix}-ecs-task-role"

  # Trust policy: Allows ECS tasks to assume this role
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name = "${var.name_prefix}-ecs-task-role"
  }
}

# ============================================================================
# S3 Access Policy
# ============================================================================
# Allows your Flask application to read/write files to S3
# WHY: S3 is used to serve artwork images and file assets. Your Flask app
# needs permission to:
# - Upload new artwork (PutObject)
# - Serve artwork to users (GetObject)
# - Delete old files (DeleteObject)
# - List files in the bucket (ListBucket)
#
# IMPORTANT: This assumes you'll create an S3 bucket named
# "library-of-babble-prod-uploads" (or similar based on name_prefix)
# The bucket isn't created by this Terraform code yet - you'll need to
# add that separately when you're ready to use S3 for artwork storage.
resource "aws_iam_role_policy" "s3_access" {
  name = "${var.name_prefix}-s3-access"
  role = aws_iam_role.task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",    # Upload files
          "s3:GetObject",    # Download/serve files
          "s3:DeleteObject", # Remove files
          "s3:ListBucket"    # List bucket contents
        ]
        Resource = [
          "arn:aws:s3:::${var.name_prefix}-uploads",      # Bucket itself
          "arn:aws:s3:::${var.name_prefix}-uploads/*"     # All objects in bucket
        ]
      }
    ]
  })
}

# ============================================================================
# OUTPUTS - IAM Role ARNs exported to compute module
# ============================================================================
output "task_execution_role_arn" {
  description = "ARN of the ECS task execution role - used to start containers"
  value       = aws_iam_role.task_execution.arn
}

output "task_role_arn" {
  description = "ARN of the ECS task role - used by running application"
  value       = aws_iam_role.task.arn
}
