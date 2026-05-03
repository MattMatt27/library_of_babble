# ============================================================================
# TERRAFORM OUTPUTS
# ============================================================================
# Output values from infrastructure deployment
# Use: terraform output <name> to get individual values
# ============================================================================

# ============================================================================
# ECR (Docker Registry)
# ============================================================================
output "ecr_repository_url" {
  description = "ECR repository URL - use for docker push commands"
  value       = module.ecr.repository_url
}

output "ecr_repository_name" {
  description = "ECR repository name - needed for GitHub Actions secrets"
  value       = module.ecr.repository_name
}

# ============================================================================
# ECS (Container Service)
# ============================================================================
output "ecs_cluster_name" {
  description = "ECS cluster name - needed for GitHub Actions secrets"
  value       = module.compute.cluster_name
}

output "ecs_service_name" {
  description = "ECS service name - needed for GitHub Actions secrets"
  value       = module.compute.service_name
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group name - view logs in AWS Console"
  value       = module.compute.log_group_name
}

# ============================================================================
# Database
# ============================================================================
output "db_endpoint" {
  description = "RDS database endpoint (host:port)"
  value       = module.database.db_endpoint
}

output "db_name" {
  description = "Name of the database"
  value       = module.database.db_name
}

# ============================================================================
# Networking
# ============================================================================
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.networking.vpc_id
}

# ============================================================================
# Storage (S3)
# ============================================================================
output "static_bucket_name" {
  description = "S3 bucket name for static assets"
  value       = module.storage.bucket_name
}

output "static_url" {
  description = "Base URL for static assets - use as STATIC_STORAGE_URL env var"
  value       = module.storage.static_url
}

# ============================================================================
# Helpful Commands
# ============================================================================
output "next_steps" {
  description = "What to do after Terraform completes"
  value = <<-EOT

  Infrastructure deployed successfully!

  Next Steps:

  1. Create the DATABASE_URL parameter in Parameter Store:
     aws ssm put-parameter \
       --name "/library-of-babble/prod/database-url" \
       --value "postgresql://${var.db_username}:<PASSWORD>@${module.database.db_endpoint}/${module.database.db_name}" \
       --type SecureString

  2. Get ECS task public IP:
     CLUSTER="${module.compute.cluster_name}"
     TASK=$(aws ecs list-tasks --cluster $CLUSTER --query 'taskArns[0]' --output text)
     ENI=$(aws ecs describe-tasks --cluster $CLUSTER --tasks $TASK --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' --output text)
     aws ec2 describe-network-interfaces --network-interface-ids $ENI --query 'NetworkInterfaces[0].Association.PublicIp' --output text

  3. Configure CloudFlare DNS:
     Point your domain to the ECS task IP

  4. Verify deployment:
     Visit https://${var.domain_name}

  EOT
}
