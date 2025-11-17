.PHONY: help install install-dev test lint format type-check clean docker-up docker-down db-init

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install production dependencies
	cd backend && pip install -e .

install-dev: ## Install development dependencies
	cd backend && pip install -e ".[dev]"
	pip install pre-commit
	pre-commit install

test: ## Run tests
	cd backend && pytest tests/ -v

test-cov: ## Run tests with coverage
	cd backend && pytest tests/ -v --cov=src --cov-report=html --cov-report=term

lint: ## Run linting (ruff)
	cd backend && ruff check src/ ai/ scripts/

format: ## Format code (ruff)
	cd backend && ruff format src/ ai/ scripts/

type-check: ## Run type checking (mypy)
	cd backend && mypy src/ ai/

check: lint type-check ## Run all checks (lint + type-check)

clean: ## Clean generated files
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -r {} + 2>/dev/null || true
	rm -rf backend/htmlcov backend/.coverage backend/coverage.xml

docker-up: ## Start Docker services
	docker compose up -d

docker-down: ## Stop Docker services
	docker compose down

db-init: ## Initialize database schema
	cd backend && python -m src.db.init_db

db-reset: docker-down docker-up ## Reset database (stop, start, init)
	sleep 5
	$(MAKE) db-init

setup: install-dev db-init ## Complete setup (install dev deps + init DB)

