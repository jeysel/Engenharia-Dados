# Terraform - Infraestrutura AWS

Infraestrutura como código para o pipeline SSP-SC usando Terraform.

## 📦 Recursos Criados

### Networking
- **VPC** - Rede isolada (10.0.0.0/16)
- **2 Public Subnets** - Para NAT Gateway
- **2 Private Subnets** - Para RDS (Multi-AZ)
- **Internet Gateway** - Acesso internet
- **NAT Gateway** - Para subnets privadas
- **VPC Endpoint S3** - Acesso S3 sem NAT 

### Storage
- **S3 Bucket** - Data Lake com pastas:
  - `raw/` - Dados brutos (Bronze)
  - `processed/silver/` - Dados limpos
  - `processed/gold/` - Dados agregados
  - `logs/` - Logs de acesso
  - `backups/` - Backups

##  Como Usar

### 1. Pré-requisitos

```bash
# Instalar Terraform Linux
wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg

echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list

apt-get update

apt-get install terraform  

terraform version

# Configurar AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"

apt-get update && apt-get install -y unzip
unzip awscliv2.zip
./aws/install
aws --version

aws configure
AWS Access Key ID: YOUR_KEY
AWS Secret Access Key: YOUR_SECRET
Default region name: us-east-1
Default output format: json
```
aws sts get-caller-identity

ls -la ~/.aws/
cat ~/.aws/credentials
cat ~/.aws/config

### 2. Inicializar Terraform

```bash
cd terraform

# Inicializar providers e modules
terraform init
```

### 3. Criar Arquivo de Variáveis

```bash
# terraform.tfvars
cp terraform.tfvars.example terraform.tfvars

# Editar com seus valores
nano terraform.tfvars
```

**Exemplo de `terraform.tfvars`:**

```hcl
# terraform.tfvars
aws_region = "us-east-1"
environment = "dev"
project_name = "ssp-sc-pipeline"

# Database
db_username = "admin"
db_password = "CHANGE_ME_SECURE_PASSWORD_HERE"  # Mínimo 8 caracteres
db_instance_class = "db.t3.micro"
db_allocated_storage = 20
db_backup_retention_days = 7
db_publicly_accessible = false  # true para acesso externo (dev apenas)
enable_multi_az = false  # true para produção

# S3
s3_bucket_prefix = "ssp-sc-data-lake"
enable_versioning = true
enable_encryption = true
lifecycle_glacier_days = 90
lifecycle_expiration_days = 365

# Network
vpc_cidr = "10.0.0.0/16"
allowed_cidr_blocks = ["0.0.0.0/0"]  # ⚠️ Restringir em produção!

# Tags
tags = {
  Team = "Data Engineering"
  Purpose = "SSP-SC Pipeline"
}
```

### 4. Validar Configuração

```bash
# Validar sintaxe
terraform validate

# Formatar código
terraform fmt -recursive

# Ver plano de execução
terraform plan

# Ver apenas um resumo
terraform plan -compact-warnings
```

### 5. Aplicar Infraestrutura

```bash
# Aplicar mudanças
terraform apply

# Confirmar quando solicitado
# Digite 'yes'

# Método profissional 
terraform plan -out=tfplan (salva em: /workspace/search-ssp-sc/terraform/tfplan)
terraform show tfplan  # revisa
terraform apply tfplan

# Destruir tudo depois dos testes
terraform destroy

# Verificar se excluiu 
echo "=== Recursos Terraform ===" && terraform state list

# Veja tudo que o Terraform criou
terraform state list

# Ou use AWS CLI
aws ec2 describe-vpcs --region us-east-1
aws rds describe-db-instances --region us-east-1
aws s3 ls
```

### 6. Ver Outputs

```bash
# Ver todos outputs
terraform output

# Ver output específico
terraform output rds_endpoint
terraform output s3_bucket_name
terraform output database_connection_string
```

## 🔐 Segurança

### Best Practices Implementadas

✅ VPC isolada
✅ RDS em subnets privadas
✅ Criptografia em repouso (S3 + RDS)
✅ S3 bucket policy restritiva
✅ Security Groups mínimos
✅ No hard-coded credentials
✅ Backup automático habilitado
✅ Versionamento S3
✅ CloudWatch Alarms

### Para Produção

1. **Restringir CIDR blocks**
```hcl
allowed_cidr_blocks = ["10.0.0.0/8"]  # Apenas rede interna
```

2. **Habilitar deletion protection**
```hcl
deletion_protection = true  # RDS
```

3. **Usar Secrets Manager**
```hcl
# Armazenar senhas no Secrets Manager
```

4. **Habilitar audit logs**
```hcl
enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
```

5. **Multi-AZ para RDS**
```hcl
enable_multi_az = true
```

## 📚 Documentação Adicional

- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [RDS Best Practices](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_BestPractices.html)
- [S3 Lifecycle Policies](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html)

## 🤝 Contribuindo

Ao modificar Terraform:
1. Execute `terraform fmt`
2. Execute `terraform validate`
3. Documente mudanças no `CHANGELOG.md`
4. Atualize custos estimados

---