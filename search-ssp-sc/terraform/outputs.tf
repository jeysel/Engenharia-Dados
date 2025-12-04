# Terraform Outputs

# S3 Outputs
output "s3_bucket_name" {
  description = "Nome do bucket S3 do Data Lake"
  value       = aws_s3_bucket.data_lake.id
}

output "s3_bucket_arn" {
  description = "ARN do bucket S3"
  value       = aws_s3_bucket.data_lake.arn
}

output "s3_bucket_region" {
  description = "Região do bucket S3"
  value       = aws_s3_bucket.data_lake.region
}

output "s3_access_policy_arn" {
  description = "ARN da IAM policy para acesso ao S3"
  value       = aws_iam_policy.s3_access.arn
}

# RDS Outputs
output "rds_endpoint" {
  description = "Endpoint do RDS PostgreSQL"
  value       = aws_db_instance.postgres.endpoint
}

output "rds_address" {
  description = "Address do RDS (sem porta)"
  value       = aws_db_instance.postgres.address
}

output "rds_port" {
  description = "Porta do RDS"
  value       = aws_db_instance.postgres.port
}

output "rds_database_name" {
  description = "Nome do database"
  value       = aws_db_instance.postgres.db_name
}

output "rds_username" {
  description = "Username do database"
  value       = aws_db_instance.postgres.username
  sensitive   = true
}

output "database_connection_string" {
  description = "String de conexão PostgreSQL (sem senha)"
  value       = "postgresql://${aws_db_instance.postgres.username}:PASSWORD@${aws_db_instance.postgres.endpoint}/${aws_db_instance.postgres.db_name}"
  sensitive   = true
}

# VPC Outputs
output "vpc_id" {
  description = "ID da VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "IDs das subnets públicas"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs das subnets privadas"
  value       = aws_subnet.private[*].id
}

output "nat_gateway_ip" {
  description = "IP público do NAT Gateway"
  value       = aws_eip.nat.public_ip
}

# Security Group Outputs
output "rds_security_group_id" {
  description = "ID do Security Group do RDS"
  value       = aws_security_group.rds.id
}

# CloudWatch Outputs
output "cloudwatch_alarm_names" {
  description = "Nomes dos CloudWatch Alarms criados"
  value = {
    cpu         = aws_cloudwatch_metric_alarm.database_cpu.alarm_name
    storage     = aws_cloudwatch_metric_alarm.database_storage.alarm_name
    connections = aws_cloudwatch_metric_alarm.database_connections.alarm_name
  }
}

# Informações Úteis
output "deployment_info" {
  description = "Informações úteis sobre o deployment"
  value = {
    environment           = var.environment
    region                = var.aws_region
    project_name          = var.project_name
    rds_instance_class    = var.db_instance_class
    rds_storage_gb        = var.db_allocated_storage
    rds_multi_az          = var.enable_multi_az
    s3_versioning_enabled = var.enable_versioning
  }
}

# Comandos úteis
output "useful_commands" {
  description = "Comandos úteis para conectar aos recursos"
  value = {
    psql_connect = "psql postgresql://${var.db_username}:YOUR_PASSWORD@${aws_db_instance.postgres.endpoint}/${var.db_name}"
    aws_s3_ls    = "aws s3 ls s3://${aws_s3_bucket.data_lake.id}/"
    aws_s3_sync  = "aws s3 sync ./data s3://${aws_s3_bucket.data_lake.id}/raw/"
  }
}
