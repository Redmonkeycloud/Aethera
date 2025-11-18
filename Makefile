.PHONY: help start start-background stop redis celery api services check install

# Default target
help:
	@echo "AETHERA Service Management"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  start           Start all services (foreground)"
	@echo "  start-background Start all services (background)"
	@echo "  stop            Stop all services"
	@echo "  redis           Start Redis server only"
	@echo "  celery          Start Celery worker only"
	@echo "  api             Start FastAPI server only"
	@echo "  services        Start all services (alias for start)"
	@echo "  check           Check if services are running"
	@echo "  install         Install dependencies"
	@echo ""

# Configuration
REDIS_PORT ?= 6379
API_PORT ?= 8000
API_HOST ?= localhost

# Detect OS
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Linux)
	START_SCRIPT = scripts/start_services.sh
	STOP_SCRIPT = scripts/stop_services.sh
endif
ifeq ($(UNAME_S),Darwin)
	START_SCRIPT = scripts/start_services.sh
	STOP_SCRIPT = scripts/stop_services.sh
endif
ifeq ($(OS),Windows_NT)
	START_SCRIPT = scripts/start_services.ps1
	STOP_SCRIPT = scripts/stop_services.ps1
endif

# Start all services
start:
	@echo "Starting all services..."
ifeq ($(OS),Windows_NT)
	@powershell -ExecutionPolicy Bypass -File $(START_SCRIPT)
else
	@bash $(START_SCRIPT)
endif

start-background:
	@echo "Starting all services in background..."
ifeq ($(OS),Windows_NT)
	@powershell -ExecutionPolicy Bypass -File $(START_SCRIPT) -Background
else
	@bash $(START_SCRIPT) --background
endif

services: start

# Stop all services
stop:
	@echo "Stopping all services..."
ifeq ($(OS),Windows_NT)
	@if exist stop_services.ps1 powershell -ExecutionPolicy Bypass -File scripts/stop_services.ps1
else
	@if [ -f scripts/stop_services.sh ]; then bash scripts/stop_services.sh; fi
endif
	@echo "Note: You may need to manually stop services if stop script doesn't exist"

# Start individual services
redis:
	@echo "Starting Redis..."
	@redis-server --port $(REDIS_PORT) || echo "Redis already running or not installed"

celery:
	@echo "Starting Celery worker..."
	@celery -A backend.src.workers.celery_app worker --loglevel=info

api:
	@echo "Starting FastAPI server..."
	@uvicorn backend.src.api.app:app --host $(API_HOST) --port $(API_PORT) --reload

# Check services
check:
	@echo "Checking services..."
	@echo ""
	@echo "Redis:"
	@redis-cli -p $(REDIS_PORT) ping 2>/dev/null && echo "  ✓ Running" || echo "  ✗ Not running"
	@echo ""
	@echo "Celery:"
	@celery -A backend.src.workers.celery_app inspect active 2>/dev/null > /dev/null && echo "  ✓ Running" || echo "  ✗ Not running"
	@echo ""
	@echo "FastAPI:"
	@curl -s http://$(API_HOST):$(API_PORT)/docs > /dev/null 2>&1 && echo "  ✓ Running" || echo "  ✗ Not running"
	@echo ""

# Install dependencies
install:
	@echo "Installing dependencies..."
	@cd backend && pip install -e .
	@echo "✓ Dependencies installed"

