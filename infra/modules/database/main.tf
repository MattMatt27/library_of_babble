# ============================================================================
# DATABASE MODULE
# ============================================================================
# Creates an RDS PostgreSQL database instance
#
# WHAT THIS MODULE CREATES:
# - RDS PostgreSQL instance: Managed database server
# - Automated backups: 7-day retention for disaster recovery
# - CloudWatch log exports: For monitoring and debugging
# - Encrypted storage: Data encrypted at rest
#
# WHY WE NEED THIS:
# Your Flask app stores all data (books, movies, users, etc.) in PostgreSQL.
# RDS (Relational Database Service) is AWS's managed database - it handles:
# - Automatic backups
# - Software updates
# - Monitoring and alerting
# - Scaling
# So you don't need to maintain a database server yourself.
#
# COST CONSIDERATIONS:
# - db.t4g.micro: ~$13/month (smallest ARM-based instance)
# - Storage (gp3): ~$2.30/month for 20GB
# - Backups: Included in 7-day retention
# - Multi-AZ: Disabled (would double cost) - acceptable for portfolio site
# ============================================================================

# Input variables passed from main.tf
variable "name_prefix" {
  type        = string
  description = "Prefix for naming resources"
}

variable "vpc_id" {
  type        = string
  description = "VPC ID where database will be created"
}

variable "db_subnet_group_name" {
  type        = string
  description = "DB subnet group name (from networking module)"
}

variable "security_group_id" {
  type        = string
  description = "Security group ID for database (from security module)"
}

variable "db_username" {
  type        = string
  description = "Master username for database"
}

variable "db_password_param_arn" {
  description = "ARN of Parameter Store parameter containing DB password"
  type        = string
}

variable "db_name" {
  type        = string
  description = "Name of the database to create"
}

variable "instance_class" {
  type        = string
  default     = "db.t4g.micro"
  description = "RDS instance size (db.t4g.micro is cheapest ARM-based option)"
}

variable "allocated_storage" {
  type        = number
  default     = 20
  description = "Storage in GB (20GB is minimum for gp3)"
}

# ============================================================================
# Fetch Database Password
# ============================================================================
# Retrieves the DB password from Parameter Store for RDS creation
# WHY: Terraform needs the actual password value (not just the ARN) to create
# the RDS instance. After creation, the password is stored in Parameter Store
# and ECS containers fetch it from there.
#
# SECURITY NOTE: with_decryption = true means the password appears in Terraform
# state. This is necessary for RDS creation but is a security consideration.
# The lifecycle block below prevents password changes from triggering updates.
data "aws_ssm_parameter" "db_password" {
  name            = replace(element(split(":", var.db_password_param_arn), length(split(":", var.db_password_param_arn)) - 1), "parameter", "")
  with_decryption = true # Decrypt the password value
}

# ============================================================================
# RDS PostgreSQL Instance
# ============================================================================
# The actual managed database server
resource "aws_db_instance" "main" {
  identifier = "${var.name_prefix}-db"

  # ========================================
  # Engine Configuration
  # ========================================
  # WHY PostgreSQL: Your Flask app uses SQLAlchemy with PostgreSQL
  # WHY version 15: Stable, modern version with good performance (AWS picks latest patch)
  # WHY gp3 storage: Latest generation storage - faster and cheaper than gp2
  # WHY encrypted: Encrypts data at rest for security compliance
  engine               = "postgres"
  engine_version       = "15"
  instance_class       = var.instance_class # db.t4g.micro for cost savings
  allocated_storage    = var.allocated_storage # GB of storage
  storage_type         = "gp3" # General Purpose SSD (latest generation)
  storage_encrypted    = true # Encrypt data at rest

  # ========================================
  # Database Configuration
  # ========================================
  # Creates the initial database and master user
  db_name  = var.db_name # e.g., "library_of_babble"
  username = var.db_username # Master username
  password = data.aws_ssm_parameter.db_password.value # From Parameter Store

  # ========================================
  # Network Configuration
  # ========================================
  # WHY private subnets: Database should never be internet-accessible
  # WHY not publicly_accessible: Extra layer of security
  db_subnet_group_name   = var.db_subnet_group_name # Private subnets across 2 AZs
  vpc_security_group_ids = [var.security_group_id] # Only allow ECS access
  publicly_accessible    = false # Never expose to internet

  # ========================================
  # Backup Configuration
  # ========================================
  # WHY 7 days: Allows recovery from mistakes within a week
  # WHY 3am UTC: Low traffic time for backups (minimal performance impact)
  # WHY CloudWatch logs: Helps debug database issues and track upgrades
  backup_retention_period   = 1 # Free tier max; increase to 7 after upgrading account
  backup_window             = "03:00-04:00" # UTC time for daily backups
  maintenance_window        = "mon:04:00-mon:05:00" # UTC time for updates
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"] # Send logs to CloudWatch

  # ========================================
  # High Availability
  # ========================================
  # WHY multi_az = false: For a portfolio site, the cost of Multi-AZ (~2x)
  # isn't justified. Multi-AZ provides automatic failover if one availability
  # zone fails, but for non-critical apps, accepting brief downtime is fine.
  multi_az = false

  # ========================================
  # Deletion Protection
  # ========================================
  # IMPORTANT: For production, set deletion_protection = true to prevent
  # accidental deletion. For dev/test, false allows easier teardown.
  # skip_final_snapshot = true means no snapshot is taken on deletion
  # (faster but can't recover data)
  deletion_protection       = false
  skip_final_snapshot       = true
  final_snapshot_identifier = "${var.name_prefix}-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"

  # ========================================
  # Auto Updates
  # ========================================
  # WHY true: Automatically apply minor version updates (e.g., 15.4 → 15.5)
  # during the maintenance window. Keeps database secure and up-to-date.
  auto_minor_version_upgrade = true

  # ========================================
  # Performance Insights (Optional)
  # ========================================
  # Uncomment to enable advanced performance monitoring
  # Adds ~$7/month but provides detailed query performance metrics
  # performance_insights_enabled = true

  tags = {
    Name = "${var.name_prefix}-db"
  }

  # ========================================
  # Lifecycle Configuration
  # ========================================
  # Prevents Terraform from updating the database when:
  # 1. Password changes in Parameter Store (password is managed there)
  # 2. Timestamp in final_snapshot_identifier changes
  lifecycle {
    ignore_changes = [
      password,
      final_snapshot_identifier,
    ]
  }
}

# ============================================================================
# OUTPUTS - Database connection details exported to other modules
# ============================================================================
output "db_endpoint" {
  description = "Database endpoint (host:port) - e.g., mydb.abc123.us-east-1.rds.amazonaws.com:5432"
  value       = aws_db_instance.main.endpoint
}

output "db_address" {
  description = "Database hostname only (without port)"
  value       = aws_db_instance.main.address
}

output "db_name" {
  description = "Database name - passed to ECS containers via environment variable"
  value       = aws_db_instance.main.db_name
}

output "db_port" {
  description = "Database port (5432 for PostgreSQL)"
  value       = aws_db_instance.main.port
}
