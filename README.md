[![CI](https://github.com/Kinpa07/orderflow/actions/workflows/ci.yml/badge.svg)](https://github.com/Kinpa07/orderflow/actions/workflows/ci.yml)

# OrderFlow

A multi-tenant order processing pipeline built with Python, FastAPI, PostgreSQL, and Redis. Orders are submitted via HTTP, processed asynchronously through a validation → payment reservation → fulfillment pipeline, and tenants receive signed webhook notifications on every state transition.

## Architecture

```
┌─────────────┐     HTTP      ┌─────────────────┐
│  CLI client │ ──────────── │   FastAPI (API)  │
│  (orderflow)│              │   :8000          │
└─────────────┘              └────────┬─────────┘
                                      │ Redis Stream
                              ┌───────▼──────────┐
                              │  order-processor  │
                              │  :8001            │
                              └───────┬───────────┘
                                      │ HMAC-signed POST
                                      ▼
                              Tenant webhook URL

         PostgreSQL ◄──── both services
         Redis       ◄──── both services (cache + Streams)
         Prometheus  ◄──── both services (/metrics)
         Grafana     ◄──── Prometheus
```

**Request flow:**
1. Tenant submits an order via `POST /tenants/{id}/orders/`
2. API validates the order, writes it to Postgres, and publishes an event to a Redis Stream
3. The order-processor consumes the event, advances the order through `pending → processing → shipped`, and commits each transition to Postgres
4. On each transition, the order-processor POSTs a signed webhook to the tenant's registered URL
5. If delivery fails after retries, the payload is stored in the dead-letter table

## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI, Pydantic, Starlette |
| Database | PostgreSQL 17, SQLAlchemy (async), Alembic |
| Cache / Events | Redis 7 (tenant config cache, rate limiting, Streams) |
| Observability | Prometheus, Grafana, structlog (structured JSON logging) |
| Infrastructure | Docker Compose, GitHub Actions CI/CD |
| CLI | orderflow (typer + httpx) |

## Quick Start

**Prerequisites:** Docker Desktop, Python 3.13, Poetry

```bash
git clone https://github.com/Kinpa07/orderflow
cd orderflow
cp .env.example .env
docker compose up -d
```

Migrations run automatically on first start. Verify the stack is healthy:

```bash
curl http://localhost:8000/health
# {"status":"OK"}
```

Install the CLI:

```bash
poetry install
```

Run the 30-second demo:

```bash
bash demo.sh
```

## Running Tests and CI

Tests require the Docker Compose stack to be running (integration and system tests hit real Postgres and Redis).

```bash
# Mirror the full CI pipeline locally — lint + type-check + all tests
make ci

# Individual stages
make lint          # ruff check
make type-check    # mypy --strict
make test          # all tests with coverage report

# Individual test layers
make test-unit         # no services needed
make test-integration  # requires db + redis (make services-up)
make test-system       # requires full stack (make up)

# Start only db + redis (faster than the full stack for integration tests)
make services-up
```

`make ci` runs the same stages in the same order as the GitHub Actions pipeline — if it passes locally, the pipeline passes. Coverage must stay above 80%.

## Dashboards

With the stack running, open Grafana at **http://localhost:3000** (admin / admin).

Navigate to **Dashboards → OrderFlow**. Set the time range to **Last 15 minutes**.

To populate the dashboard with realistic data, run the load generator:

```bash
python load_test.py
```

This creates tenants, submits orders in concurrent waves, injects 4xx traffic, and runs a local webhook receiver — giving every panel real data within about 3 minutes.

**Reading the dashboard:**
- **Request rate / error rate**: healthy system shows steady request rate, error rate near zero
- **HTTP latency (p95)**: spikes here indicate slow middleware or blocked event loop
- **Order pipeline throughput**: should drain at roughly 1 order/second per processor instance
- **Cache hit rate**: should be above 90% after the first request per tenant
- **Webhook health**: delivery rate drops and dead-letter depth climbs when the tenant endpoint is unreachable
- **Consumer lag**: non-zero lag means the order-processor is falling behind the Stream — look at order processing duration next

---

## CLI Reference

All commands accept `ORDERFLOW_API_URL` as an environment variable to point at a non-default host.

### Tenants

```bash
# Create a tenant (returns the API key — save it)
orderflow tenants create --name "Acme Corp" --email "ops@acme.com"

# Create with custom config and webhook
orderflow tenants create \
  --name "Acme Corp" \
  --email "ops@acme.com" \
  --config '{"maximum_price": 500.0}' \
  --webhook-url "https://acme.com/hooks/orders"
```

### Orders

```bash
# Submit an order
orderflow orders submit \
  --tenant 1 \
  --api-key <key> \
  --data '{"price": 49.99}'

# Check a specific order
orderflow orders status --tenant 1 --order 42 --api-key <key>

# List orders (supports pagination and status filter)
orderflow orders list --tenant 1 --api-key <key>
orderflow orders list --tenant 1 --api-key <key> --status pending --limit 50

# Watch orders update in real time (polls every 2s, Ctrl+C to stop)
orderflow orders watch --tenant 1 --api-key <key>
```

### Webhooks

```bash
# Inspect failed webhook deliveries for a tenant
orderflow webhooks dead-letter --tenant 1 --api-key <key>
```

---

## API Reference

Base URL: `http://localhost:8000`

Interactive docs: `http://localhost:8000/docs`

### Authentication

All tenant-scoped endpoints require an `api-key` header:

```
api-key: <tenant-api-key>
```

The API key is returned when the tenant is created. It is used for both authentication and HMAC signature generation on outbound webhooks. Requests without a valid key return `401`.

### Error Format

All errors — validation, auth, not found, server — return the same shape:

```json
{
  "error": {
    "code": 422,
    "message": "Validation error",
    "details": [
      {"loc": ["body", "price"], "msg": "Field required", "type": "missing"}
    ]
  }
}
```

`details` is an empty array for non-validation errors.

### Rate Limiting

15 requests per minute per tenant (configurable via `RATE_LIMIT` env var). Exceeded requests return `429`:

```json
{"error": {"code": 429, "message": "Rate limit exceeded", "details": []}}
```

### Request Limits

- Maximum request body: **1 MB** (configurable via `MAX_BODY_SIZE` env var). Exceeded requests return `413`.
- Maximum page size: **100** (configurable via `MAX_PAGE_SIZE` env var). Values above the cap return `422`.

### Endpoints

#### `POST /tenants/`
Create a tenant. No authentication required.

```bash
curl -X POST http://localhost:8000/tenants/ \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Acme Corp",
    "contact_name": "Jane Smith",
    "email": "jane@acme.com",
    "phone": "+1-555-0100",
    "config": {"maximum_price": 500.0},
    "webhook_url": "https://acme.com/hooks/orders"
  }'
```

Response includes `api_key` — this is only shown once.

#### `PUT /tenants/{id}`
Update tenant config or webhook URL. Requires `api-key`.

#### `POST /tenants/{id}/orders/`
Submit an order. Requires `api-key`. The order is rejected if `price` exceeds the tenant's `maximum_price`.

```bash
curl -X POST http://localhost:8000/tenants/1/orders/ \
  -H "api-key: <key>" \
  -H "Content-Type: application/json" \
  -d '{"price": 49.99}'
```

#### `GET /tenants/{id}/orders/`
List orders with optional filtering and cursor-based pagination. Requires `api-key`.

Query params: `status`, `limit` (default 20, max 100), `cursor_id`, `cursor_created_at`.

Cursor-based pagination is preferred over offset for large datasets — it remains stable under concurrent inserts. Use `next_cursor` and `next_cursor_created_at` from the response to fetch the next page.

#### `GET /tenants/{id}/orders/{order_id}`
Get a single order by ID. Requires `api-key`.

#### `GET /tenants/{id}/webhooks/dead-letter`
List failed webhook deliveries for the tenant, newest first. Requires `api-key`.

Response:
```json
{
  "items": [
    {
      "id": 1,
      "tenant_id": 1,
      "order_id": 42,
      "webhook_url": "https://acme.com/hooks/orders",
      "payload": "{\"order_id\": 42, \"status\": \"shipped\", ...}",
      "error_message": "HTTP 500",
      "failed_at": "2026-05-22T14:11:40.016289"
    }
  ],
  "total": 1
}
```

#### `GET /health`
Health check. Returns `{"status": "OK"}`. No authentication.

---

## Webhook System

When a tenant registers a `webhook_url`, the order-processor delivers a signed POST request on every order state transition (`pending → processing`, `processing → shipped`).

### Payload

```json
{
  "order_id": 42,
  "tenant_id": 1,
  "price": 49.99,
  "status": "shipped",
  "timestamp": "2026-05-22T14:11:32.993174+00:00"
}
```

### Signature Verification

Each request includes an `X-Signature` header containing an HMAC-SHA256 hex digest. The signature is computed over the raw JSON payload bytes using the tenant's API key as the secret.

To verify in Python:

```python
import hashlib
import hmac

def verify_signature(payload_bytes: bytes, api_key: str, received_sig: str) -> bool:
    expected = hmac.new(
        key=api_key.encode(),
        msg=payload_bytes,
        digestmod=hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, received_sig)
```

**Important:** always use `hmac.compare_digest` for the comparison, never `==`. Constant-time comparison prevents timing attacks.

### Retry Behaviour

Failed deliveries (non-2xx response or connection error) are retried with exponential backoff:

| Attempt | Delay before retry |
|---|---|
| 1 | immediate |
| 2 | 1 second |
| 3 | 2 seconds |

After all attempts are exhausted, the payload is written to the dead-letter table and the `dead_letter_queue_depth` Prometheus metric increments. Retrieve failed deliveries via `GET /tenants/{id}/webhooks/dead-letter` or `orderflow webhooks dead-letter`.

Your endpoint should return a 2xx status code to acknowledge receipt. Any non-2xx triggers a retry.

---

## API Versioning

The API currently has no version prefix. The strategy when a breaking change is needed is **path-based versioning**: introduce a `/v2/` prefix for the new version while keeping `/v1/` (or the unversioned path) alive for existing consumers during a deprecation window.

Breaking changes that would trigger a new version: removing or renaming a response field, changing authentication mechanics, altering error response shape, or changing pagination behaviour in a way that invalidates existing cursors.

Non-breaking changes (adding optional fields, adding new endpoints, adding new query parameters) do not require a version bump.

---

## Design Decisions

**Cursor-based pagination over offset.** `GET /tenants/{id}/orders/` uses `(created_at, id)` as a composite cursor. Offset pagination (`LIMIT x OFFSET y`) becomes inconsistent under concurrent inserts — rows shift as new orders are added mid-pagination. Cursor-based pagination is stable regardless of write activity.

**Redis for dual duty.** Redis serves as both a cache (tenant configs, rate limit counters) and a message broker (order events via Streams). The tradeoff is operational simplicity over strict separation — a single Redis failure takes both functions down simultaneously. For the current scale this is acceptable; at higher scale these would be separate instances.

**Webhook delivery is non-blocking.** The order-processor spawns webhook delivery as a background task (`asyncio.create_task`) so a slow or unreachable tenant endpoint does not block order processing. The consequence is that webhook delivery order is not guaranteed relative to other tenants' deliveries.

**HMAC signature uses the API key as the secret.** This avoids storing a separate webhook secret per tenant. The tradeoff is that rotating an API key also rotates the webhook secret, requiring tenants to update their verification logic. An explicit per-webhook secret would be cleaner but adds complexity.

**Connection pooling is explicit.** Both the Postgres engine and Redis client use explicit pool settings driven by environment variables (`DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `REDIS_MAX_CONNECTIONS`). Library defaults are intentional but opaque — explicit config makes capacity planning visible and testable.
