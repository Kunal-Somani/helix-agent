.PHONY: help install dev test lint format build docker-build docker-up docker-down clean

help:
	@echo "LLM Quiz Solver - Development Commands"
	@echo "========================================"
	@echo "install         - Install Python dependencies"
	@echo "dev             - Start development server with auto-reload"
	@echo "test            - Run test suite with coverage"
	@echo "lint            - Run code linters (flake8, mypy)"
	@echo "format          - Format code with black"
	@echo "docker-build    - Build Docker image"
	@echo "docker-up       - Start all services with docker-compose"
	@echo "docker-down     - Stop all services"
	@echo "clean           - Clean cache and temp files"
	@echo "requirements    - Update and freeze dependencies"

install:
	pip install -r backend/requirements.txt

dev:
	cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest backend/tests -v --cov=backend/app --cov-report=html --cov-report=term

lint:
	flake8 backend/app --max-line-length=120
	mypy backend/app --ignore-missing-imports

format:
	black backend/app --line-length=120

docker-build:
	docker build -f backend/Dockerfile -t llm-quiz-solver:latest .

docker-up:
	docker-compose up -d
	@echo "Services started:"
	@echo "  Backend:   http://localhost:8000"
	@echo "  Prometheus: http://localhost:9090"
	@echo "  Grafana:   http://localhost:3000"
	@echo "  Loki:      http://localhost:3100"

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f backend

docker-ps:
	docker-compose ps

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete

requirements:
	pip install --upgrade pip setuptools wheel
	pip list --outdated

shell:
	cd backend && python

version:
	@echo "Python: $$(python --version)"
	@echo "Docker: $$(docker --version)"
	@echo "Poetry: $$(poetry --version 2>/dev/null || echo 'not installed')"
