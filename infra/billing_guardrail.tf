# ============================================================================
# BILLING / BLAST-RADIUS GUARDRAIL
# ============================================================================
# A deny-only policy attached to the admin IAM user that caps how much damage
# a compromised admin credential could do, WITHOUT being a hard dollar cap
# (AWS has no such thing). Explicit Deny overrides the user's AdministratorAccess.
#
# It does two things:
#   1. Region lock — denies everything outside the primary region (var.aws_region,
#      us-east-1), except truly global services. Kills the "spin up GPU fleets
#      across every region" abuse pattern.
#   2. Blocks expensive compute launches (EC2 instances, SageMaker, EMR) even in
#      the primary region — services this stack never uses (it's Fargate).
#
# SAFETY (validated via `aws iam simulate-custom-policy`):
#   * All real app / deploy / terraform actions in us-east-1 stay ALLOWED.
#   * iam:* and sts:* are ALWAYS allowed (in the NotAction exemption), so this
#     policy can never lock the admin user out of removing it. Root login is a
#     further backstop (IAM denies don't apply to root).
#   * Attached only to the admin USER — it does NOT affect the ECS task role or
#     the OIDC deploy role, so it cannot break the running site or deploys.
#
# To disable temporarily:
#   aws iam detach-user-policy --user-name library-of-babble-admin \
#     --policy-arn <this policy arn>
# ============================================================================

variable "admin_user_name" {
  type        = string
  description = "IAM user (with AdministratorAccess) the guardrail is attached to"
  default     = "library-of-babble-admin"
}

resource "aws_iam_policy" "billing_guardrail" {
  name        = "${local.name_prefix}-billing-guardrail"
  description = "Blast-radius cap: region-lock + deny expensive compute. Detachable; iam/sts always allowed."

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "DenyOutsidePrimaryRegion"
        Effect = "Deny"
        # Global services are exempt from the region lock (they have no regional
        # home / route through us-east-1). iam + sts are here so the guardrail is
        # always removable — do not drop them.
        NotAction = [
          "iam:*", "sts:*", "organizations:*", "account:*", "support:*",
          "trustedadvisor:*", "health:*", "budgets:*", "ce:*", "cur:*",
          "cloudfront:*", "route53:*", "route53domains:*", "globalaccelerator:*",
          "waf:*", "wafv2:*", "waf-regional:*", "shield:*", "kms:*"
        ]
        Resource = "*"
        Condition = {
          StringNotEquals = { "aws:RequestedRegion" = var.aws_region }
        }
      },
      {
        Sid    = "DenyExpensiveComputeAnywhere"
        Effect = "Deny"
        Action = [
          "ec2:RunInstances",
          "sagemaker:CreateTrainingJob",
          "sagemaker:CreateEndpoint",
          "sagemaker:CreateNotebookInstance",
          "sagemaker:CreateProcessingJob",
          "emr:RunJobFlow",
        ]
        Resource = "*"
      }
    ]
  })

  tags = {
    Name = "${local.name_prefix}-billing-guardrail"
  }
}

resource "aws_iam_user_policy_attachment" "billing_guardrail" {
  user       = var.admin_user_name
  policy_arn = aws_iam_policy.billing_guardrail.arn
}

output "billing_guardrail_policy_arn" {
  description = "ARN of the billing/blast-radius guardrail policy (detach to disable)"
  value       = aws_iam_policy.billing_guardrail.arn
}
