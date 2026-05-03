# infra/variables.tf
# Variable definitions for Library of Babble infrastructure
# Sensitive values are stored in AWS Parameter Store, not here

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "library-of-babble"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "db_username" {
  description = "Database master username (not sensitive)"
  type        = string
  default     = "dbadmin"
}

variable "docker_image" {
  description = "Docker image URL (defaults to ECR repository created by Terraform)"
  type        = string
  default     = "" # Will use ECR repository URL if not specified
}

variable "cloudflare_zone_id" {
  description = "CloudFlare zone ID for your domain (optional - leave empty if not using CloudFlare)"
  type        = string
  default     = ""
}

variable "domain_name" {
  description = "Your domain name (e.g., mattflathers.com). Leave empty to use ECS public IP directly."
  type        = string
  default     = ""
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t4g.micro"
}

variable "db_allocated_storage" {
  description = "RDS allocated storage in GB (can only increase, never decrease)"
  type        = number
  default     = 20
}

variable "ecs_task_cpu" {
  description = "ECS task CPU units (256 = 0.25 vCPU)"
  type        = number
  default     = 256
}

variable "ecs_task_memory" {
  description = "ECS task memory in MB"
  type        = number
  default     = 512
}

variable "ecs_desired_count" {
  description = "Number of ECS tasks to run"
  type        = number
  default     = 1
}
