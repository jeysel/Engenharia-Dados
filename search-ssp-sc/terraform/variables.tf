# Variáveis de Configuração do Terraform

variable "aws_region" {
  description = "Região AWS onde os recursos serão criados"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Ambiente de deployment (dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment deve ser dev, staging ou prod"
  }
}

variable "project_name" {
  description = "Nome do projeto"
  type        = string
  default     = "ssp-sc-pipeline"
}

# S3 Variables
variable "s3_bucket_prefix" {
  description = "Prefixo para nome do bucket S3"
  type        = string
  default     = "ssp-sc-data-lake"
}

variable "enable_versioning" {
  description = "Habilitar versionamento no S3"
  type        = bool
  default     = true
}

variable "enable_encryption" {
  description = "Habilitar criptografia no S3"
  type        = bool
  default     = true
}

variable "lifecycle_glacier_days" {
  description = "Dias para mover objetos para Glacier"
  type        = number
  default     = 90
}

variable "lifecycle_expiration_days" {
  description = "Dias para deletar objetos antigos"
  type        = number
  default     = 365
}

# RDS Variables
variable "db_instance_class" {
  description = "Classe da instância RDS"
  type        = string
  default     = "db.t3.micro"

  validation {
    condition     = can(regex("^db\\.", var.db_instance_class))
    error_message = "Instance class deve começar com 'db.'"
  }
}

variable "db_engine_version" {
  description = "Versão do PostgreSQL"
  type        = string
  default     = "16.1"
}

variable "db_name" {
  description = "Nome do banco de dados"
  type        = string
  default     = "ssp_sc_db"
}

variable "db_username" {
  description = "Username do banco de dados"
  type        = string
  default     = "admin"
  sensitive   = true
}

variable "db_password" {
  description = "Senha do banco de dados (use AWS Secrets Manager em produção)"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.db_password) >= 8
    error_message = "Senha deve ter no mínimo 8 caracteres"
  }
}

variable "db_allocated_storage" {
  description = "Armazenamento alocado em GB"
  type        = number
  default     = 20

  validation {
    condition     = var.db_allocated_storage >= 20 && var.db_allocated_storage <= 1000
    error_message = "Storage deve estar entre 20 e 1000 GB"
  }
}

variable "db_backup_retention_days" {
  description = "Dias de retenção de backup"
  type        = number
  default     = 7

  validation {
    condition     = var.db_backup_retention_days >= 1 && var.db_backup_retention_days <= 35
    error_message = "Backup retention deve estar entre 1 e 35 dias"
  }
}

variable "db_publicly_accessible" {
  description = "RDS publicamente acessível (use false em produção)"
  type        = bool
  default     = false
}

variable "enable_multi_az" {
  description = "Habilitar Multi-AZ para alta disponibilidade"
  type        = bool
  default     = false
}

# Network Variables
variable "vpc_cidr" {
  description = "CIDR block para VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "allowed_cidr_blocks" {
  description = "CIDR blocks permitidos para acessar o RDS"
  type        = list(string)
  default     = ["0.0.0.0/0"] # CUIDADO: Aberto para mundo. Ajuste em produção!
}

# Tags
variable "tags" {
  description = "Tags adicionais para recursos"
  type        = map(string)
  default     = {}
}
