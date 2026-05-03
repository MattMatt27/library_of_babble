# ============================================================================
# STORAGE MODULE
# ============================================================================
# Creates S3 bucket for static assets (images, artwork, etc.)
#
# WHAT THIS MODULE CREATES:
# - S3 bucket for static files
# - Bucket policy for public read access
# - CORS configuration for web access
#
# WHY WE NEED THIS:
# Static images (5.7 GB) are too large to bundle in Docker containers.
# S3 provides cheap, scalable storage with high availability.
# In production, images are served from S3; in development, from local /static.
# ============================================================================

variable "name_prefix" {
  type        = string
  description = "Prefix for naming resources"
}

variable "aws_region" {
  type        = string
  description = "AWS region"
}

variable "bucket_name" {
  type        = string
  description = "Override bucket name (use to adopt an existing bucket)"
  default     = ""
}

# ============================================================================
# S3 Bucket
# ============================================================================
# tfsec:ignore:aws-s3-encryption-customer-key — SSE-S3 is sufficient for
#   public static assets. CMK adds cost without security benefit here.
# tfsec:ignore:aws-s3-enable-bucket-logging — Bucket is fronted by Cloudflare;
#   request logs live there. S3 access logs would be redundant.
resource "aws_s3_bucket" "static" {
  bucket = var.bucket_name != "" ? var.bucket_name : "${var.name_prefix}-static"

  tags = {
    Name = var.bucket_name != "" ? var.bucket_name : "${var.name_prefix}-static"
  }
}

# ============================================================================
# Server-Side Encryption (SSE-S3)
# ============================================================================
# AWS enables SSE-S3 by default for new buckets, but declaring it explicitly
# documents intent and satisfies static-analysis tools.
resource "aws_s3_bucket_server_side_encryption_configuration" "static" {
  bucket = aws_s3_bucket.static.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# ============================================================================
# Versioning
# ============================================================================
# Protects against accidental overwrites/deletes of artwork files.
resource "aws_s3_bucket_versioning" "static" {
  bucket = aws_s3_bucket.static.id

  versioning_configuration {
    status = "Enabled"
  }
}

# ============================================================================
# Public Access Configuration
# ============================================================================
# Block ACL-based public access (defense-in-depth) but allow our bucket policy
# to grant public read for serving static assets.
# tfsec:ignore:aws-s3-block-public-policy — Required false; the bucket's
#   public-read policy below is the intended access mechanism.
# tfsec:ignore:aws-s3-no-public-buckets — Required false for the same reason.
resource "aws_s3_bucket_public_access_block" "static" {
  bucket = aws_s3_bucket.static.id

  block_public_acls       = true
  block_public_policy     = false
  ignore_public_acls      = true
  restrict_public_buckets = false
}

# ============================================================================
# Bucket Policy - Public Read
# ============================================================================
resource "aws_s3_bucket_policy" "static" {
  bucket = aws_s3_bucket.static.id

  # Ensure public access block is configured first
  depends_on = [aws_s3_bucket_public_access_block.static]

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.static.arn}/*"
      }
    ]
  })
}

# ============================================================================
# CORS Configuration
# ============================================================================
# Allow web browsers to load images from S3
resource "aws_s3_bucket_cors_configuration" "static" {
  bucket = aws_s3_bucket.static.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "HEAD"]
    allowed_origins = ["*"]  # Restrict to your domain in production if needed
    expose_headers  = ["ETag"]
    max_age_seconds = 3600
  }
}

# ============================================================================
# OUTPUTS
# ============================================================================
output "bucket_name" {
  description = "Name of the S3 bucket"
  value       = aws_s3_bucket.static.id
}

output "bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.static.arn
}

output "bucket_regional_domain_name" {
  description = "Regional domain name of the bucket (for direct S3 access)"
  value       = aws_s3_bucket.static.bucket_regional_domain_name
}

output "static_url" {
  description = "Base URL for static assets"
  value       = "https://${aws_s3_bucket.static.bucket_regional_domain_name}"
}
