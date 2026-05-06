# OrderFlow

A multi-tenant order processing pipeline built with Python, FastAPI, PostgreSQL, and Redis.

## What it does

OrderFlow allows businesses (tenants) to submit orders via API and process them through a configurable validation → payment reservation → fulfillment pipeline. Operators can monitor system health through real-time metrics and dashboards. Tenants receive order state updates via webhooks.

## Status

🚧 Under active development

## Tech Stack

- **API**: FastAPI, Pydantic
- **Database**: PostgreSQL, SQLAlchemy (async), Alembic
- **Cache / Events**: Redis (cache + Streams)
- **Observability**: Prometheus, Grafana, structlog
- **Infrastructure**: Docker Compose, GitHub Actions CI/CD
- **CLI**: orderflow (typer)

## Setup

Documentation coming in a later stage of development.