# ============================================================================
# ECR MODULE
# ============================================================================
# Creates an Elastic Container Registry (ECR) repository to store Docker images
#
# WHAT THIS MODULE CREATES:
# - ECR Repository: Private Docker image registry in AWS
# - Lifecycle Policy: Automatically deletes old untagged images to save storage costs
#
# WHY WE NEED THIS:
# ECR is AWS's Docker registry (like Docker Hub, but private to your account).
# Your GitHub Actions workflow pushes Docker images here, and ECS pulls them
# from here to run containers.
#
# COST NOTE: $0.10/GB per month for storage
# - Typical Flask app image: ~500MB = $0.05/month
# - Lifecycle policy keeps costs low by removing old images
# ============================================================================

# Input variables passed from main.tf
variable "name_prefix" {
  type        = string
  description = "Prefix for naming resources"
}

# ============================================================================
# ECR Repository
# ============================================================================
# Private Docker image registry
# WHY: Stores your Flask app Docker images securely in AWS
# tfsec:ignore:aws-ecr-enforce-immutable-repository — The deploy workflow
#   pushes a moving `:latest` tag on every release, which requires MUTABLE.
#   Each release also gets a unique SemVer tag (which is effectively immutable
#   in practice since release tags aren't reused). Could be tightened by
#   dropping `:latest` and referencing images by SHA, but that's a separate
#   refactor of deploy.yml and the task definition.
resource "aws_ecr_repository" "app" {
  name                 = var.name_prefix
  image_tag_mutability = "MUTABLE" # Allows overwriting tags like "latest"

  # Image scanning on push detects vulnerabilities
  # WHY: Scans Docker images for security issues automatically
  # COST NOTE: First 30 days free, then ~$0.09 per image scan (minimal)
  image_scanning_configuration {
    scan_on_push = true
  }

  # Encryption at rest using AWS KMS
  # WHY: Encrypts Docker images for security compliance
  encryption_configuration {
    encryption_type = "AES256" # Default AWS encryption (free)
  }

  tags = {
    Name = "${var.name_prefix}-ecr"
  }
}

# ============================================================================
# Lifecycle Policy
# ============================================================================
# Automatically deletes old untagged images to save storage costs
# WHY: Each time you push a new image, old layers may become untagged.
# Without cleanup, storage costs grow over time. This policy keeps only
# the most recent 3 untagged images and deletes the rest.
resource "aws_ecr_lifecycle_policy" "app" {
  repository = aws_ecr_repository.app.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 3 untagged images"
        selection = {
          tagStatus   = "untagged"
          countType   = "imageCountMoreThan"
          countNumber = 3
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Keep last 10 tagged images"
        selection = {
          tagStatus   = "tagged"
          tagPrefixList = ["v"]
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# ============================================================================
# OUTPUTS - ECR repository details
# ============================================================================
output "repository_url" {
  description = "Full URL of the ECR repository (use this for docker push)"
  value       = aws_ecr_repository.app.repository_url
}

output "repository_arn" {
  description = "ARN of the ECR repository"
  value       = aws_ecr_repository.app.arn
}

output "repository_name" {
  description = "Name of the ECR repository"
  value       = aws_ecr_repository.app.name
}

output "registry_id" {
  description = "Registry ID (AWS account ID)"
  value       = aws_ecr_repository.app.registry_id
}
