.PHONY: help install test lint format clean docker-up docker-down terraform-init terraform-plan terraform-apply terraform-destroy

.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo '$(BLUE)SSP-SC Data Pipeline - Available Commands$(NC)'
	@echo ''
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# =============================================================================
# Setup
# =============================================================================

install: ## Install all dependencies
	@echo '$(BLUE)Installing dependencies...$(NC)'
	pip install -r extrator/requirements.txt
	pip install -r requirements-test.txt
	@echo '$(GREEN)✓ Dependencies installed$(NC)'

install-dev: install ## Install development dependencies
	@echo '$(BLUE)Installing dev dependencies...$(NC)'
	pip install black flake8 bandit safety
	@echo '$(GREEN)✓ Dev dependencies installed$(NC)'

# =============================================================================
# Testing
# =============================================================================

test: ## Run all tests
	@echo '$(BLUE)Running tests...$(NC)'
	pytest tests/ -v

test-cov: ## Run tests with coverage
	@echo '$(BLUE)Running tests with coverage...$(NC)'
	pytest tests/ --cov=extrator --cov-report=html --cov-report=term-missing
	@echo '$(GREEN)✓ Coverage report generated in htmlcov/$(NC)'

test-unit: ## Run only unit tests
	@echo '$(BLUE)Running unit tests...$(NC)'
	pytest tests/ -v -m "not integration"

test-integration: ## Run only integration tests
	@echo '$(BLUE)Running integration tests...$(NC)'
	pytest tests/ -v -m integration

# =============================================================================
# Code Quality
# =============================================================================

lint: ## Run linters
	@echo '$(BLUE)Running flake8...$(NC)'
	flake8 extrator tests --max-line-length=127 --exclude=venv

format: ## Format code with black
	@echo '$(BLUE)Formatting code with black...$(NC)'
	black extrator tests
	@echo '$(GREEN)✓ Code formatted$(NC)'

format-check: ## Check if code is formatted
	@echo '$(BLUE)Checking code formatting...$(NC)'
	black --check extrator tests

security: ## Run security checks
	@echo '$(BLUE)Running security checks...$(NC)'
	bandit -r extrator
	safety check

# =============================================================================
# Docker
# =============================================================================

docker-up: ## Start all Docker services
	@echo '$(BLUE)Starting Docker services...$(NC)'
	docker-compose up -d
	@echo '$(GREEN)✓ Services started$(NC)'
	@echo '$(YELLOW)Dashboard: http://localhost:5000$(NC)'

docker-down: ## Stop all Docker services
	@echo '$(BLUE)Stopping Docker services...$(NC)'
	docker-compose down
	@echo '$(GREEN)✓ Services stopped$(NC)'

docker-logs: ## Show Docker logs
	docker-compose logs -f

docker-ps: ## Show running containers
	docker-compose ps

docker-rebuild: ## Rebuild and restart containers
	@echo '$(BLUE)Rebuilding containers...$(NC)'
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d
	@echo '$(GREEN)✓ Containers rebuilt$(NC)'

docker-clean: ## Remove all containers, volumes and images
	@echo '$(RED)⚠️  This will remove all data!$(NC)'
	docker-compose down -v
	docker system prune -f

# =============================================================================
# Database
# =============================================================================

db-shell: ## Open PostgreSQL shell
	docker exec -it ssp-sc-postgres psql -U user -d ssp_sc_db

db-count: ## Count records in database
	docker exec ssp-sc-postgres psql -U user -d ssp_sc_db -c "SELECT COUNT(*) FROM dados_seguranca;"

db-backup: ## Backup database
	@echo '$(BLUE)Creating database backup...$(NC)'
	docker exec ssp-sc-postgres pg_dump -U user ssp_sc_db > backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo '$(GREEN)✓ Backup created$(NC)'

# =============================================================================
# Extraction
# =============================================================================

extract: ## Run extraction (full)
	@echo '$(BLUE)Running full extraction...$(NC)'
	docker exec ssp-sc-extrator python extractor_autonomous.py

extract-test: ## Run test extraction (5 PDFs)
	@echo '$(BLUE)Running test extraction...$(NC)'
	docker exec ssp-sc-extrator python extractor_ocr_v2.py --limpar --limite=5

extract-single: ## Run extraction for single PDF
	@echo '$(BLUE)Running single PDF extraction...$(NC)'
	docker exec ssp-sc-extrator python extractor_ocr_v2.py --limpar --limite=1

# =============================================================================
# Terraform
# =============================================================================

terraform-init: ## Initialize Terraform
	@echo '$(BLUE)Initializing Terraform...$(NC)'
	cd terraform && terraform init
	@echo '$(GREEN)✓ Terraform initialized$(NC)'

terraform-validate: ## Validate Terraform configuration
	@echo '$(BLUE)Validating Terraform...$(NC)'
	cd terraform && terraform validate
	@echo '$(GREEN)✓ Configuration valid$(NC)'

terraform-plan: ## Show Terraform execution plan
	@echo '$(BLUE)Generating Terraform plan...$(NC)'
	cd terraform && terraform plan

terraform-apply: ## Apply Terraform changes
	@echo '$(BLUE)Applying Terraform changes...$(NC)'
	cd terraform && terraform apply
	@echo '$(GREEN)✓ Infrastructure deployed$(NC)'

terraform-destroy: ## Destroy Terraform infrastructure
	@echo '$(RED)⚠️  This will destroy all infrastructure!$(NC)'
	cd terraform && terraform destroy

terraform-output: ## Show Terraform outputs
	cd terraform && terraform output

terraform-fmt: ## Format Terraform files
	@echo '$(BLUE)Formatting Terraform files...$(NC)'
	cd terraform && terraform fmt -recursive
	@echo '$(GREEN)✓ Files formatted$(NC)'

# =============================================================================
# CI/CD
# =============================================================================

ci-local: lint test ## Run CI checks locally
	@echo '$(GREEN)✓ All CI checks passed$(NC)'

pre-commit: format lint test ## Run pre-commit checks
	@echo '$(GREEN)✓ Ready to commit$(NC)'

# =============================================================================
# Clean
# =============================================================================

clean: ## Clean temporary files
	@echo '$(BLUE)Cleaning temporary files...$(NC)'
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.pyo' -delete
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name htmlcov -exec rm -rf {} +
	find . -type f -name .coverage -delete
	rm -rf .tox
	@echo '$(GREEN)✓ Cleaned$(NC)'

clean-all: clean docker-clean ## Clean everything including Docker
	@echo '$(GREEN)✓ Everything cleaned$(NC)'

# =============================================================================
# Development
# =============================================================================

dev-setup: install-dev docker-up extract-test ## Setup development environment
	@echo '$(GREEN)✓ Development environment ready!$(NC)'
	@echo '$(YELLOW)Dashboard: http://localhost:5000$(NC)'

dev-test: format lint test ## Run development tests
	@echo '$(GREEN)✓ Development tests passed$(NC)'

# =============================================================================
# Documentation
# =============================================================================

docs-serve: ## Serve documentation locally
	@echo '$(BLUE)Opening documentation...$(NC)'
	@echo 'Opening README.md...'
	@if command -v open > /dev/null; then open README.md; \
	elif command -v xdg-open > /dev/null; then xdg-open README.md; \
	else echo 'Please open README.md manually'; fi

# =============================================================================
# Monitoring
# =============================================================================

status: ## Show status of all components
	@echo '$(BLUE)=== Docker Containers ===$(NC)'
	@docker-compose ps || echo 'Docker not running'
	@echo ''
	@echo '$(BLUE)=== Database Stats ===$(NC)'
	@docker exec ssp-sc-postgres psql -U user -d ssp_sc_db -c "SELECT COUNT(*) as total_records FROM dados_seguranca;" 2>/dev/null || echo 'Database not available'
	@echo ''
	@echo '$(BLUE)=== Terraform Status ===$(NC)'
	@cd terraform && terraform workspace show 2>/dev/null || echo 'Terraform not initialized'

health: ## Check health of all services
	@echo '$(BLUE)Checking service health...$(NC)'
	@curl -s http://localhost:5000/health > /dev/null && echo '$(GREEN)✓ Dashboard OK$(NC)' || echo '$(RED)✗ Dashboard Down$(NC)'
	@docker exec ssp-sc-postgres pg_isready -U user > /dev/null 2>&1 && echo '$(GREEN)✓ Database OK$(NC)' || echo '$(RED)✗ Database Down$(NC)'
