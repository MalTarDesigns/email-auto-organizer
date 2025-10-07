.PHONY: help build up down logs shell-backend shell-frontend migrate migrate-create test clean

help:
	@echo "Email Triage System - Development Commands"
	@echo ""
	@echo "make build          - Build all Docker containers"
	@echo "make up             - Start all services"
	@echo "make down           - Stop all services"
	@echo "make logs           - View logs from all services"
	@echo "make shell-backend  - Open shell in backend container"
	@echo "make shell-frontend - Open shell in frontend container"
	@echo "make migrate        - Run database migrations"
	@echo "make migrate-create - Create new migration"
	@echo "make test           - Run tests"
	@echo "make clean          - Remove all containers and volumes"

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

shell-backend:
	docker-compose exec backend /bin/bash

shell-frontend:
	docker-compose exec frontend /bin/sh

migrate:
	docker-compose exec backend alembic upgrade head

migrate-create:
	@read -p "Enter migration name: " name; \
	docker-compose exec backend alembic revision --autogenerate -m "$$name"

test:
	docker-compose exec backend pytest

clean:
	docker-compose down -v
	docker system prune -f
