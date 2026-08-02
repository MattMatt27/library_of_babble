# ============================================================================
# GITHUB OIDC MODULE
# ============================================================================
# Lets GitHub Actions authenticate to AWS with a short-lived, federated token
# instead of a long-lived IAM access key stored in GitHub secrets.
#
# WHY: today the deploy workflow uses a static AWS_ACCESS_KEY_ID /
# AWS_SECRET_ACCESS_KEY belonging to an AdministratorAccess user. If that key
# leaks (laptop, CI log, compromised action) an attacker owns the whole
# account. With OIDC there is NO stored secret — GitHub presents a signed
# token, AWS trades it for temporary credentials, and this role grants only
# the handful of ECR + ECS actions the deploy actually performs.
#
# This module is additive: creating it changes nothing about the existing
# key-based deploy until deploy.yml is switched to use the role.
# ============================================================================

variable "github_repo" {
  type        = string
  description = "GitHub repo allowed to assume the deploy role, as owner/name"
}

variable "subject_claims" {
  type        = list(string)
  description = <<-EOT
    Allowed GitHub OIDC `sub` claims (which refs/environments may assume the
    role). Defaults to any ref in the repo so a manual smoke-test workflow can
    validate OIDC before cutover; tighten to tags once the release deploy is
    switched over (e.g. repo:owner/name:ref:refs/tags/*).
  EOT
  default     = null
}

variable "name_prefix" {
  type        = string
  description = "Prefix for naming resources"
}

variable "ecr_repository_arn" {
  type        = string
  description = "ARN of the ECR repository the workflow pushes images to"
}

variable "ecs_cluster_arn" {
  type        = string
  description = "ARN of the ECS cluster (for DescribeServices)"
}

variable "ecs_service_arn" {
  type        = string
  description = "ARN of the ECS service the workflow force-deploys"
}

locals {
  subs = var.subject_claims != null ? var.subject_claims : ["repo:${var.github_repo}:*"]
}

# ----------------------------------------------------------------------------
# OIDC identity provider for GitHub Actions
# ----------------------------------------------------------------------------
# One per account. client_id ("audience") is sts.amazonaws.com, matching what
# aws-actions/configure-aws-credentials requests. The thumbprints are GitHub's
# well-known intermediate CA fingerprints; AWS also validates the live cert
# chain for this provider, so thumbprint rotation is not a concern here.
resource "aws_iam_openid_connect_provider" "github" {
  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
  thumbprint_list = [
    "6938fd4d98bab03faadb97b34396831e3780aea1",
    "1c58a3a8518e8759bf075b76b750d4f2df264fca",
  ]

  tags = {
    Name = "${var.name_prefix}-github-oidc"
  }
}

# ----------------------------------------------------------------------------
# Deploy role assumed by GitHub Actions via OIDC
# ----------------------------------------------------------------------------
resource "aws_iam_role" "github_deploy" {
  name = "${var.name_prefix}-github-deploy"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = { Federated = aws_iam_openid_connect_provider.github.arn }
        Action    = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          # Audience must be sts.amazonaws.com...
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          # ...and the token must come from an allowed ref of THIS repo.
          StringLike = {
            "token.actions.githubusercontent.com:sub" = local.subs
          }
        }
      }
    ]
  })

  tags = {
    Name = "${var.name_prefix}-github-deploy"
  }
}

# ----------------------------------------------------------------------------
# Least-privilege deploy policy — exactly what deploy.yml does, nothing more:
#   * ECR login + push image to the one repo
#   * ECS force-new-deployment + wait on the one service
# No EC2 / IAM / other services — a compromised CI run cannot launch a fleet.
# ----------------------------------------------------------------------------
resource "aws_iam_role_policy" "github_deploy" {
  name = "${var.name_prefix}-github-deploy"
  role = aws_iam_role.github_deploy.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "EcrAuth"
        Effect   = "Allow"
        Action   = ["ecr:GetAuthorizationToken"] # must be on "*" (account-wide token)
        Resource = "*"
      },
      {
        Sid    = "EcrPushPull"
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload",
          "ecr:PutImage",
        ]
        Resource = var.ecr_repository_arn
      },
      {
        Sid      = "EcsDeploy"
        Effect   = "Allow"
        Action   = ["ecs:UpdateService", "ecs:DescribeServices"]
        Resource = [var.ecs_service_arn]
        Condition = {
          ArnEquals = { "ecs:cluster" = var.ecs_cluster_arn }
        }
      }
    ]
  })
}

output "deploy_role_arn" {
  description = "ARN of the GitHub Actions deploy role (set as role-to-assume in the workflow)"
  value       = aws_iam_role.github_deploy.arn
}
