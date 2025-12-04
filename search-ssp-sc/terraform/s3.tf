# Data Lake S3 Bucket

# Gera nome único do bucket
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

locals {
  bucket_name = "${var.s3_bucket_prefix}-${var.environment}-${random_id.bucket_suffix.hex}"
}

# Bucket principal do Data Lake
resource "aws_s3_bucket" "data_lake" {
  bucket = local.bucket_name

  tags = merge(
    var.tags,
    {
      Name        = "SSP-SC Data Lake"
      Description = "Armazena dados brutos e processados da SSP-SC"
    }
  )
}

# Versionamento
resource "aws_s3_bucket_versioning" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  versioning_configuration {
    status = var.enable_versioning ? "Enabled" : "Disabled"
  }
}

# Criptografia
resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Bloquear acesso público
resource "aws_s3_bucket_public_access_block" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle policies
resource "aws_s3_bucket_lifecycle_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  # Raw data (Bronze) - Mover para Glacier após 90 dias
  rule {
    id     = "raw-data-lifecycle"
    status = "Enabled"

    filter {
      prefix = "raw/"
    }

    transition {
      days          = var.lifecycle_glacier_days
      storage_class = "GLACIER"
    }

    expiration {
      days = var.lifecycle_expiration_days
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }

  # Processed data (Silver/Gold) - Manter mais tempo
  rule {
    id     = "processed-data-lifecycle"
    status = "Enabled"

    filter {
      prefix = "processed/"
    }

    transition {
      days          = var.lifecycle_glacier_days * 2 # 180 dias
      storage_class = "GLACIER"
    }

    noncurrent_version_expiration {
      noncurrent_days = 60
    }
  }

  # Logs - Deletar após 30 dias
  rule {
    id     = "logs-lifecycle"
    status = "Enabled"

    filter {
      prefix = "logs/"
    }

    expiration {
      days = 30
    }
  }
}

# Organização de pastas (prefixes)
resource "aws_s3_object" "folders" {
  for_each = toset([
    "raw/",
    "raw/ssp-sc/",
    "processed/",
    "processed/silver/",
    "processed/gold/",
    "logs/",
    "backups/"
  ])

  bucket       = aws_s3_bucket.data_lake.id
  key          = each.value
  content_type = "application/x-directory"
}

# Bucket para logs de acesso (opcional mas recomendado)
resource "aws_s3_bucket" "logs" {
  bucket = "${local.bucket_name}-logs"

  tags = merge(
    var.tags,
    {
      Name        = "SSP-SC Access Logs"
      Description = "Logs de acesso ao bucket principal"
    }
  )
}

resource "aws_s3_bucket_public_access_block" "logs" {
  bucket = aws_s3_bucket.logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Logging
resource "aws_s3_bucket_logging" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  target_bucket = aws_s3_bucket.logs.id
  target_prefix = "access-logs/"
}

# IAM Policy para acesso ao bucket
resource "aws_iam_policy" "s3_access" {
  name        = "${var.project_name}-s3-access-${var.environment}"
  description = "Permite acesso ao bucket S3 do Data Lake"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Resource = aws_s3_bucket.data_lake.arn
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.data_lake.arn}/*"
      }
    ]
  })

  tags = var.tags
}
