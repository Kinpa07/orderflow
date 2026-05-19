import hashlib
import hmac
import json
from collections.abc import Callable
from typing import Any
from unittest.mock import patch

import httpx
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from models.order import Order
from models.order_status import OrderStatus
from models.tenant import Tenant
from schemas.tenant import TenantCreate


async def test_webhook_delivery_sends_signed_payload(
    client: AsyncClient,
    redis_client: Redis,
    make_tenant: Callable[..., TenantCreate],
    db_session: AsyncSession,
) -> None:
    tenant_response = await client.post(
        "/tenants/",
        json=make_tenant(webhook_url="http://mock-webhook/webhook").model_dump(),
    )
    api_key = tenant_response.json()["api_key"]
    tenant_id = tenant_response.json()["id"]

    receiver = FastAPI()
    captured: list[dict[str, Any]] = []

    @receiver.post("/webhook")
    async def capture(request: Request) -> dict[str, str]:
        captured.append(
            {"body": await request.body(), "headers": dict(request.headers)}
        )
        return {"status": "ok"}

    real_async_client = httpx.AsyncClient

    def make_asgi_client() -> httpx.AsyncClient:
        return real_async_client(transport=ASGITransport(app=receiver))

    with patch("order_processor.webhook.httpx.AsyncClient", make_asgi_client):
        from order_processor.webhook import deliver_webhook

        tenant = Tenant(
            id=tenant_id,
            company_name="Test",
            contact_name="Test",
            email="test@test.com",
            phone="123",
            config={},
            api_key=api_key,
            webhook_url="http://mock-webhook/webhook",
        )
        order = Order(
            id=1, tenant_id=tenant_id, price=50.0,
            status=OrderStatus.PROCESSING, priority=4,
        )

        await deliver_webhook(tenant, order)

    assert len(captured) == 1
    body_bytes = captured[0]["body"]
    payload = json.loads(body_bytes)
    assert payload["order_id"] == 1
    assert payload["status"] == "processing"

    expected_sig = hmac.new(api_key.encode(), body_bytes, hashlib.sha256).hexdigest()
    assert captured[0]["headers"]["x-signature"] == expected_sig
