.PHONY: help install setup-env up down logs dev test test-auth test-resource test-client test-e2e test-e2e-cc demo-cc coverage migrate seed seed-local clean build

help:
	@echo "OAuth2 Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install        Install Python dependencies for all services"
	@echo "  make setup-env      Create .env from .env.example"
	@echo ""
	@echo "Running Services:"
	@echo "  make up             Start all services with Docker Compose"
	@echo "  make down           Stop all services"
	@echo "  make dev            Start services with hot-reload"
	@echo "  make logs           View logs from all services"
	@echo "  make logs-auth      View logs from auth-server only"
	@echo ""
	@echo "Testing:"
	@echo "  make test           Run all tests"
	@echo "  make test-auth      Run authorization server tests"
	@echo "  make test-resource  Run resource server tests"
	@echo "  make test-client    Run client app tests"
	@echo "  make test-e2e       Run end-to-end Authorization Code flow test"
	@echo "  make test-e2e-cc    Run end-to-end Client Credentials flow test"
	@echo "  make demo-cc        Run Client Credentials demo script"
	@echo "  make coverage       Generate test coverage report"
	@echo ""
	@echo "Database:"
	@echo "  make migrate        Run database migrations"
	@echo "  make seed           Seed database with test data (Docker)"
	@echo "  make seed-local     Seed local SQLite database (no Docker)"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean          Remove containers and volumes"
	@echo "  make clean-all      Deep clean (remove images too)"
	@echo ""
	@echo "Build:"
	@echo "  make build          Build Docker images"

install:
	pip install -r auth-server/requirements.txt
	pip install -r resource-server/requirements.txt
	pip install -r client-app/requirements.txt

setup-env:
	@if [ -f .env ]; then \
		echo ".env file already exists"; \
	else \
		cp .env.example .env; \
		echo ".env created from .env.example - update with your values"; \
	fi

build:
	docker-compose build

up:
	docker-compose up -d
	@echo ""
	@echo "Services started:"
	@echo "  Client App:         http://localhost:5001"
	@echo "  Auth Server:        http://localhost:5000"
	@echo "  Resource Server:    http://localhost:5002"
	@echo ""
	@echo "View logs with: make logs"

down:
	docker-compose down

logs:
	docker-compose logs -f

logs-auth:
	docker-compose logs -f auth-server

logs-resource:
	docker-compose logs -f resource-server

logs-client:
	docker-compose logs -f client-app

dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Database operations
migrate:
	docker-compose exec auth-server alembic upgrade head
	@echo "Migrations complete"

seed:
	docker-compose exec auth-server python scripts/seed.py
	@echo "Database seeded with test data"

seed-local:
	python scripts/seed.py
	@echo "Local database seeded"

# Testing
test:
	pytest -v tests/
	@echo ""
	@echo "All tests completed. Use 'make coverage' to generate a detailed report."

test-auth:
	pytest tests/auth_server/ -v

test-resource:
	pytest tests/resource_server/ -v

test-client:
	pytest tests/client_app/ -v

test-e2e:
	pytest tests/e2e/test_auth_code_flow.py -v -s

test-e2e-cc:
	pytest tests/e2e/test_client_credentials_flow.py -v -s

demo-cc:
	python scripts/service_client.py

coverage:
	coverage report -m && coverage html #TODO review report output
	@echo ""
	@echo "Coverage report generated in htmlcov/index.html"

# Cleanup
clean:
	docker-compose down -v
	@echo "Containers and volumes removed"

clean-all:
	docker-compose down -v
	docker system prune -f
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	@echo "Deep clean completed"

# Utility
ps:
	docker-compose ps

shell-auth:
	docker-compose exec auth-server /bin/bash

shell-resource:
	docker-compose exec resource-server /bin/bash

shell-client:
	docker-compose exec client-app /bin/bash

db-shell:
	docker-compose exec postgres psql -U oauth2_user -d oauth2

# Health checks
health:
	@echo "Checking service health..."
	@curl -s http://localhost:5000/health | jq . || echo "Auth Server: DOWN"
	@curl -s http://localhost:5002/health | jq . || echo "Resource Server: DOWN"
	@curl -s http://localhost:5001/health | jq . || echo "Client App: DOWN"
