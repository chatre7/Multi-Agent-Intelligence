# Makefile for Multi-Agent Intelligence Platform

.PHONY: help build up down restart logs clean test pull-models

# Default target
help:
	@echo "Multi-Agent Intelligence Platform - Docker Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  make build        - Build all Docker images"
	@echo "  make up           - Start all services"
	@echo "  make down         - Stop all services"
	@echo "  make restart      - Restart all services"
	@echo "  make logs         - View logs from all services"
	@echo "  make clean        - Stop and remove all containers, networks, and volumes"
	@echo "  make pull-models  - Pull required Ollama models"
	@echo "  make test         - Run backend tests"
	@echo "  make shell-backend - Open shell in backend container"
	@echo "  make shell-frontend - Open shell in frontend container"
	@echo ""

# Build all images
build:
	docker-compose build

# Start all services
up:
	docker-compose up -d
	@echo ""
	@echo "✅ Services started!"
	@echo "Frontend: http://localhost:5173"
	@echo "Backend API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"
	@echo ""
	@echo "Don't forget to pull Ollama models: make pull-models"

# Start all services with logs
up-logs:
	docker-compose up

# Stop all services
down:
	docker-compose down

# Restart all services
restart:
	docker-compose restart

# View logs
logs:
	docker-compose logs -f

# View backend logs only
logs-backend:
	docker-compose logs -f backend

# View frontend logs only
logs-frontend:
	docker-compose logs -f frontend

# View ollama logs only
logs-ollama:
	docker-compose logs -f ollama

# Clean everything (including volumes)
clean:
	docker-compose down -v
	docker system prune -f

# Pull Ollama models
pull-models:
	@echo "Pulling Ollama models..."
	docker-compose exec ollama ollama pull gpt-oss:120b-cloud
	docker-compose exec ollama ollama pull nomic-embed-text
	@echo "✅ Models downloaded!"

# List Ollama models
list-models:
	docker-compose exec ollama ollama list

# Run backend tests
test:
	docker-compose exec backend pytest tests/unit -v

# Run backend tests with coverage
test-coverage:
	docker-compose exec backend pytest tests/unit --cov=src --cov-report=html

# Open backend shell
shell-backend:
	docker-compose exec backend bash

# Open frontend shell
shell-frontend:
	docker-compose exec frontend sh

# Check service status
status:
	docker-compose ps

# View resource usage
stats:
	docker stats

# Full setup (build, start, pull models)
setup: build up
	@echo "Waiting for services to be healthy..."
	@sleep 10
	@$(MAKE) pull-models
	@echo ""
	@echo "✅ Setup complete!"
	@echo "Visit http://localhost:5173 to start using the platform"
