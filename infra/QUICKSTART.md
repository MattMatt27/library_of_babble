# Infrastructure Quick Start Guide

Complete infrastructure deployment in 5 steps - everything managed by Terraform!

## What Gets Created

One `terraform apply` creates:
- ✅ VPC with public/private subnets across 2 availability zones
- ✅ RDS PostgreSQL database (encrypted, with automated backups)
- ✅ ECR repository for Docker images
- ✅ ECS Fargate cluster and service
- ✅ Security groups (CloudFlare → ECS, ECS → RDS only)
- ✅ IAM roles with least-privilege permissions
- ✅ CloudWatch log groups

**Your repo can stay private** - no need to make it public!

## One-Time Setup (5 Steps)

### Step 1: Create AWS Parameter Store Secrets

Terraform reads secrets from Parameter Store (keeps them out of version control):

```bash
# Set your AWS region
export AWS_REGION=us-east-1

# Flask secret key (generate a random string)
aws ssm put-parameter \
  --name "/library-of-babble/prod/flask-secret-key" \
  --value "$(openssl rand -base64 32)" \
  --type "SecureString"

# Database password (generate a random password)
aws ssm put-parameter \
  --name "/library-of-babble/prod/db-password" \
  --value "$(openssl rand -base64 24)" \
  --type "SecureString"

# Spotify credentials (get from https://developer.spotify.com/)
aws ssm put-parameter \
  --name "/library-of-babble/prod/spotify-client-id" \
  --value "YOUR_SPOTIFY_CLIENT_ID" \
  --type "SecureString"

aws ssm put-parameter \
  --name "/library-of-babble/prod/spotify-client-secret" \
  --value "YOUR_SPOTIFY_CLIENT_SECRET" \
  --type "SecureString"

aws ssm put-parameter \
  --name "/library-of-babble/prod/spotify-username" \
  --value "YOUR_SPOTIFY_USERNAME" \
  --type "SecureString"

# TMDB API token (get from https://www.themoviedb.org/settings/api)
aws ssm put-parameter \
  --name "/library-of-babble/prod/tmdb-api-token" \
  --value "YOUR_TMDB_BEARER_TOKEN" \
  --type "SecureString"
```

### Step 2: Configure Terraform Variables

Create `infra/terraform.tfvars`:

```hcl
# Basic Configuration
project_name = "library-of-babble"
environment  = "prod"
aws_region   = "us-east-1"

# Database
db_username         = "dbadmin"
db_instance_class   = "db.t4g.micro"  # ~$13/month
db_allocated_storage = 20              # GB

# ECS Fargate
ecs_task_cpu    = 256  # 0.25 vCPU (~$9/month)
ecs_task_memory = 512  # 512 MB (~$2/month)
ecs_desired_count = 1  # Number of containers

# CloudFlare (optional, for now leave blank if not using)
cloudflare_zone_id = ""
domain_name        = ""

# Docker image - leave blank, Terraform will use ECR automatically
docker_image = ""
```

### Step 3: Deploy Infrastructure

```bash
cd infra

# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Deploy everything!
terraform apply
```

This takes ~10 minutes. When complete, you'll see:

```
Apply complete! Resources: 25 added, 0 changed, 0 destroyed.

Outputs:

ecr_repository_url = "123456789012.dkr.ecr.us-east-1.amazonaws.com/library-of-babble-prod"
ecs_cluster_name = "library-of-babble-prod-cluster"
ecs_service_name = "library-of-babble-prod-service"
database_endpoint = "library-of-babble-prod-db.abc123.us-east-1.rds.amazonaws.com:5432"
```

**Save these outputs!** You'll need them for the next steps.

### Step 4: Push Initial Docker Image

```bash
# From repo root, get ECR URL
ECR_URL=$(cd infra && terraform output -raw ecr_repository_url)

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin $ECR_URL

# Build and push
docker build -t library-of-babble .
docker tag library-of-babble:latest $ECR_URL:latest
docker push $ECR_URL:latest

# Tell ECS to deploy the new image
aws ecs update-service \
  --cluster $(cd infra && terraform output -raw ecs_cluster_name) \
  --service $(cd infra && terraform output -raw ecs_service_name) \
  --force-new-deployment
```

### Step 5: Setup GitHub Actions for Auto-Deploy

See [DEPLOYMENT_SETUP.md](../.github/DEPLOYMENT_SETUP.md) for complete GitHub Actions setup.

Quick version:

1. Create IAM user for GitHub Actions (instructions in deployment guide)
2. Add 6 secrets to your GitHub repository
3. Create a release → automatic deployment! 🎉

## Usage After Setup

### Deploy New Version

Just create a GitHub release:

```bash
git tag v1.0.0
git push origin v1.0.0
gh release create v1.0.0 --generate-notes
```

GitHub Actions automatically builds and deploys! 🚀

### View Logs

```bash
# Tail logs in real-time
aws logs tail /ecs/library-of-babble-prod --follow

# Or view in AWS Console
echo "https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:log-groups/log-group/\$252Fecs\$252Flibrary-of-babble-prod"
```

### Check Service Status

```bash
aws ecs describe-services \
  --cluster library-of-babble-prod-cluster \
  --services library-of-babble-prod-service \
  --query 'services[0].deployments'
```

### Connect to Running Container (Debugging)

```bash
# List running tasks
aws ecs list-tasks \
  --cluster library-of-babble-prod-cluster \
  --service library-of-babble-prod-service

# Execute command in container (get task ID from above)
aws ecs execute-command \
  --cluster library-of-babble-prod-cluster \
  --task <TASK_ID> \
  --container app \
  --interactive \
  --command "/bin/bash"
```

### Update a Secret

```bash
# Update any Parameter Store secret
aws ssm put-parameter \
  --name "/library-of-babble/prod/flask-secret-key" \
  --value "new-secret-value" \
  --type "SecureString" \
  --overwrite

# Restart ECS tasks to pick up new secret
aws ecs update-service \
  --cluster library-of-babble-prod-cluster \
  --service library-of-babble-prod-service \
  --force-new-deployment
```

## Monthly Cost Estimate

| Service | Configuration | Cost |
|---------|--------------|------|
| RDS PostgreSQL | db.t4g.micro + 20GB storage | ~$15 |
| ECS Fargate | 0.25 vCPU + 512 MB RAM | ~$11 |
| ECR | ~500MB image storage | ~$0.05 |
| NAT Gateway | Not used (using public IPs) | $0 |
| Data Transfer | Minimal for portfolio site | ~$1 |
| **Total** | | **~$27/month** |

## Teardown

To destroy all infrastructure:

```bash
cd infra
terraform destroy
```

**Warning:** This deletes everything including the database!

## Troubleshooting

### ECS tasks fail to start

Check CloudWatch logs:
```bash
aws logs tail /ecs/library-of-babble-prod --follow
```

Common issues:
- Missing Parameter Store secrets
- Database not accessible (security group issue)
- Docker image not found in ECR

### Can't push to ECR

Ensure you're logged in:
```bash
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin $(cd infra && terraform output -raw ecr_repository_url)
```

### GitHub Actions deployment fails

Check:
- All 6 GitHub secrets are set correctly
- IAM user has correct permissions
- ECR repository exists (`terraform output ecr_repository_url`)

## Next Steps

1. ✅ Setup complete!
2. Configure CloudFlare for your domain (optional)
3. Setup custom domain for ECS service (optional)
4. Enable HTTPS with ALB + ACM certificate (optional)
5. Configure CI/CD with GitHub Actions
6. Add monitoring/alerting with CloudWatch alarms

---

**Questions?** Check [DEPLOYMENT_SETUP.md](../.github/DEPLOYMENT_SETUP.md) for detailed deployment instructions.
