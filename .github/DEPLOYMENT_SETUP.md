# GitHub Actions Deployment Setup Guide

This guide walks you through setting up automated deployments to AWS ECS when you create GitHub releases.

## Prerequisites

- AWS CLI installed and configured locally
- GitHub repository (can be private - no need for public repo!)
- Terraform installed locally

## Setup Steps

### 1. Deploy Infrastructure with Terraform

Terraform will create everything you need, including the ECR repository:

```bash
cd infra

# Initialize Terraform (first time only)
terraform init

# Review what will be created
terraform plan

# Create all infrastructure
terraform apply
```

After `terraform apply` completes, you'll see outputs like:
```
ecr_repository_url = "123456789012.dkr.ecr.us-east-1.amazonaws.com/library-of-babble-prod"
ecs_cluster_name = "library-of-babble-prod-cluster"
ecs_service_name = "library-of-babble-prod-service"
```

**Save these values - you'll need them for GitHub secrets!**

### 2. Create IAM User for GitHub Actions

GitHub Actions needs AWS credentials to deploy. Create a dedicated IAM user:

```bash
# Create IAM user
aws iam create-user --user-name github-actions-deploy

# Create access key (SAVE THE OUTPUT - you'll need it for GitHub secrets)
aws iam create-access-key --user-name github-actions-deploy
```

### 3. Create IAM Policy for Deployments

Create a file called `github-actions-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ECRAccess",
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ECSAccess",
      "Effect": "Allow",
      "Action": [
        "ecs:UpdateService",
        "ecs:DescribeServices",
        "ecs:DescribeTaskDefinition",
        "ecs:RegisterTaskDefinition"
      ],
      "Resource": "*"
    },
    {
      "Sid": "PassRole",
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": "*",
      "Condition": {
        "StringLike": {
          "iam:PassedToService": "ecs-tasks.amazonaws.com"
        }
      }
    }
  ]
}
```

Then attach the policy:

```bash
# Create the policy
aws iam create-policy \
  --policy-name GitHubActionsECSDeploy \
  --policy-document file://github-actions-policy.json

# Attach to user (replace ACCOUNT_ID with your AWS account ID)
aws iam attach-user-policy \
  --user-name github-actions-deploy \
  --policy-arn arn:aws:iam::ACCOUNT_ID:policy/GitHubActionsECSDeploy
```

### 4. Add Secrets to GitHub Repository

Go to your GitHub repository → Settings → Secrets and variables → Actions → New repository secret

Add these secrets:

| Secret Name | Value | Where to Find It |
|-------------|-------|------------------|
| `AWS_ACCESS_KEY_ID` | Your IAM access key ID | From step 2 output |
| `AWS_SECRET_ACCESS_KEY` | Your IAM secret access key | From step 2 output |
| `AWS_REGION` | `us-east-1` | Or your chosen region |
| `ECR_REPOSITORY` | `library-of-babble-prod` | From Terraform output: `terraform output ecr_repository_name` |
| `ECS_CLUSTER` | `library-of-babble-prod-cluster` | From Terraform output: `terraform output ecs_cluster_name` |
| `ECS_SERVICE` | `library-of-babble-prod-service` | From Terraform output: `terraform output ecs_service_name` |

### 5. Initial Docker Image Push (One-Time)

Before the first automated deployment, you need to manually push an initial image so ECS has something to run.

First, get your ECR repository URL from Terraform:
```bash
cd infra
terraform output ecr_repository_url
# Example output: 123456789012.dkr.ecr.us-east-1.amazonaws.com/library-of-babble-prod
```

Then push your first image:

```bash
# Get your ECR repo URL (save this in a variable for convenience)
ECR_URL=$(cd infra && terraform output -raw ecr_repository_url)

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin $ECR_URL

# Build your Docker image (from repo root)
docker build -t library-of-babble .

# Tag the image for ECR
docker tag library-of-babble:latest $ECR_URL:latest

# Push to ECR
docker push $ECR_URL:latest

# Trigger ECS to pull the new image
aws ecs update-service \
  --cluster $(cd infra && terraform output -raw ecs_cluster_name) \
  --service $(cd infra && terraform output -raw ecs_service_name) \
  --force-new-deployment
```

That's it! Terraform already configured ECS to use your ECR repository automatically.

## How to Deploy

Once setup is complete, deploying is simple:

### Option 1: Create Release via GitHub UI

1. Go to your repository on GitHub
2. Click "Releases" → "Create a new release"
3. Create a new tag (e.g., `v1.0.0`)
4. Add release notes
5. Click "Publish release"
6. GitHub Actions will automatically deploy!

### Option 2: Create Release via CLI

```bash
# Create and push a tag
git tag v1.0.0
git push origin v1.0.0

# Create a release from the tag
gh release create v1.0.0 \
  --title "Release v1.0.0" \
  --notes "Description of changes"
```

### Option 3: Create Release via GitHub CLI (Shorthand)

```bash
gh release create v1.0.0 --generate-notes
```

## Monitoring Deployments

### Watch GitHub Actions

- Go to your repository → Actions tab
- You'll see the "Deploy to AWS ECS" workflow running
- Click on it to see detailed logs of each step

### Watch ECS Deployment

```bash
# Watch service events
aws ecs describe-services \
  --cluster library-of-babble-prod-cluster \
  --services library-of-babble-prod-service \
  --query 'services[0].events[:5]'

# View CloudWatch logs
aws logs tail /ecs/library-of-babble-prod --follow
```

### Check Current Running Image

```bash
# See what image is currently running
aws ecs describe-tasks \
  --cluster library-of-babble-prod-cluster \
  --tasks $(aws ecs list-tasks \
    --cluster library-of-babble-prod-cluster \
    --service library-of-babble-prod-service \
    --query 'taskArns[0]' --output text) \
  --query 'tasks[0].containers[0].image'
```

## Troubleshooting

### Deployment fails with "Permission denied"

- Check that IAM policy is attached correctly
- Verify GitHub secrets are set correctly
- Ensure the IAM user has `iam:PassRole` permission

### ECS service fails to start new tasks

- Check CloudWatch logs: `aws logs tail /ecs/library-of-babble-prod --follow`
- Verify Parameter Store secrets exist
- Check security group rules allow necessary traffic

### Docker build fails in GitHub Actions

- Check that your Dockerfile is in the repository root
- Verify all required files are committed to git
- Check GitHub Actions logs for specific error messages

### Image pushed but ECS still running old version

- Check if task definition updated: `aws ecs describe-services ...`
- Verify image tag in ECR matches what's in task definition
- Try forcing new deployment: `aws ecs update-service --cluster <cluster> --service <service> --force-new-deployment`

## Rollback

If a deployment goes wrong:

```bash
# List recent task definitions
aws ecs list-task-definitions \
  --family-prefix library-of-babble-prod \
  --sort DESC

# Update service to use previous task definition
aws ecs update-service \
  --cluster library-of-babble-prod-cluster \
  --service library-of-babble-prod-service \
  --task-definition library-of-babble-prod-task:PREVIOUS_REVISION
```

Or simply create a new release with the previous working version!

## Cost Implications

- **ECR Storage**: $0.10/GB per month (first image ~500MB = $0.05/month)
- **GitHub Actions**: 2,000 free minutes/month for private repos
- **ECS Fargate**: No additional cost for deployments (just normal running costs)

Total additional cost for CI/CD: **~$0.05-0.10/month** 🎉
