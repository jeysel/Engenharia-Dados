# RDS PostgreSQL Instance

# Security Group para RDS
resource "aws_security_group" "rds" {
  name_prefix = "${var.project_name}-rds-${var.environment}-"
  description = "Security group para RDS PostgreSQL"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "PostgreSQL access"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidr_blocks
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-rds-sg-${var.environment}"
    }
  )

  lifecycle {
    create_before_destroy = true
  }
}

# Subnet Group para RDS
resource "aws_db_subnet_group" "main" {
  name_prefix = "${var.project_name}-${var.environment}-"
  description = "Subnet group para RDS"
  subnet_ids  = aws_subnet.private[*].id

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-subnet-group-${var.environment}"
    }
  )
}

# Parameter Group (otimizações)
resource "aws_db_parameter_group" "postgres" {
  name_prefix = "${var.project_name}-postgres-${var.environment}-"
  family      = "postgres16"
  description = "Custom parameter group para PostgreSQL 16"

  # Otimizações para workloads de ETL
  parameter {
    name  = "shared_buffers"
    value = "{DBInstanceClassMemory/4096}" # 25% da RAM
  }

  parameter {
    name  = "effective_cache_size"
    value = "{DBInstanceClassMemory/2048}" # 50% da RAM
  }

  parameter {
    name  = "maintenance_work_mem"
    value = "524288" # 512MB
  }

  parameter {
    name  = "checkpoint_completion_target"
    value = "0.9"
  }

  parameter {
    name  = "wal_buffers"
    value = "16384" # 16MB
  }

  parameter {
    name  = "default_statistics_target"
    value = "100"
  }

  parameter {
    name  = "random_page_cost"
    value = "1.1" # Para SSD
  }

  parameter {
    name  = "effective_io_concurrency"
    value = "200" # Para SSD
  }

  parameter {
    name  = "work_mem"
    value = "10240" # 10MB
  }

  parameter {
    name  = "min_wal_size"
    value = "2048" # 2GB
  }

  parameter {
    name  = "max_wal_size"
    value = "8192" # 8GB
  }

  tags = var.tags

  lifecycle {
    create_before_destroy = true
  }
}

# RDS Instance
resource "aws_db_instance" "postgres" {
  identifier     = "${var.project_name}-${var.environment}"
  engine         = "postgres"
  engine_version = var.db_engine_version

  instance_class    = var.db_instance_class
  allocated_storage = var.db_allocated_storage
  storage_type      = "gp3"
  storage_encrypted = true

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  # Networking
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = var.db_publicly_accessible
  multi_az               = var.enable_multi_az

  # Backup & Maintenance
  backup_retention_period = var.db_backup_retention_days
  backup_window           = "03:00-04:00" # UTC
  maintenance_window      = "sun:04:00-sun:05:00"
  skip_final_snapshot     = var.environment == "dev" ? true : false
  final_snapshot_identifier = var.environment == "dev" ? null : "${var.project_name}-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"

  # Performance Insights
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  performance_insights_enabled    = true
  performance_insights_retention_period = 7

  # Parameter Group
  parameter_group_name = aws_db_parameter_group.postgres.name

  # Auto minor version upgrade
  auto_minor_version_upgrade = var.environment == "prod" ? false : true

  # Deletion protection
  deletion_protection = var.environment == "prod" ? true : false

  tags = merge(
    var.tags,
    {
      Name        = "${var.project_name}-rds-${var.environment}"
      Description = "PostgreSQL database para pipeline SSP-SC"
    }
  )
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "database_cpu" {
  alarm_name          = "${var.project_name}-rds-cpu-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "RDS CPU acima de 80%"

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.postgres.id
  }

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "database_storage" {
  alarm_name          = "${var.project_name}-rds-storage-${var.environment}"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "5000000000" # 5GB
  alarm_description   = "RDS com menos de 5GB livre"

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.postgres.id
  }

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "database_connections" {
  alarm_name          = "${var.project_name}-rds-connections-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "RDS com muitas conexões"

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.postgres.id
  }

  tags = var.tags
}
