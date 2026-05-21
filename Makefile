.PHONY: help lint type-check test-unit test-integration test-system test ci build up down services-up services-down migrate

help:
	@echo "Code quality:"
	@echo "  lint             Run ruff check"
	@echo "  type-check       Run mypy --strict"
	@echo ""
	@echo "Tests:"
	@echo "  test-unit        Unit tests only (no services needed)"
	@echo "  test-integration Integration tests (requires db + redis)"
	@echo "  test-system      System tests (requires full stack)"
	@echo "  test             All tests with coverage report"
	@echo ""
	@echo "CI:"
	@echo "  ci               lint + type-check + test (mirrors the pipeline)"
	@echo ""
	@echo "Docker:"
	@echo "  services-up      Start db + redis only (for running tests locally)"
	@echo "  services-down    Stop db + redis"
	@echo "  up               Start full stack"
	@echo "  down             Stop full stack"
	@echo "  build            Build the Docker image"
	@echo ""
	@echo "Database:"
	@echo "  migrate          Run alembic upgrade head"

# --- Code quality ---

lint:
	poetry run ruff check .

type-check:
	poetry run mypy --strict .

# --- Tests ---

test-unit:
	poetry run pytest tests/unit -v

test-integration:
	poetry run pytest tests/integration -v

test-system:
	poetry run pytest tests/system -v

test:
	poetry run pytest --cov=. --cov-report=term-missing -v

# --- CI gate ---
# Runs every quality stage in sequence — same order as the GitHub Actions workflow.
# If this passes locally, the pipeline should pass too.

ci: lint type-check test

# --- Docker: backing services only ---

services-up:
	docker compose up -d db redis

services-down:
	docker compose stop db redis

# --- Docker: full stack ---

up:
	docker compose up -d

down:
	docker compose down

# --- Build ---

build:
	docker build -t orderflow:local .

# --- Database ---

migrate:
	poetry run alembic upgrade head
