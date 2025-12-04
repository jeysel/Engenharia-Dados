# Configuração do Provider AWS
terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Backend para armazenar state (descomente quando tiver S3 bucket)
  # backend "s3" {
  #   bucket         = "ssp-sc-terraform-state"
  #   key            = "data-pipeline/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "terraform-state-lock"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "SSP-SC Data Pipeline"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Owner       = "Data Engineering"
      CostCenter  = "Analytics"
    }
  }
}

# Data sources
data "aws_caller_identity" "current" {}

data "aws_availability_zones" "available" {
  state = "available"
}
