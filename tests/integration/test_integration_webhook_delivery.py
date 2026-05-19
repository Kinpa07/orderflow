import hashlib
import hmac
import json
from collections.abc import Callable
from typing import Any
from unittest.mock import AsyncMock, patch

from httpx import AsyncClient
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

    captured: list[dict[str, Any]] = []

    async def mock_post(url: str, **kwargs: object) -> AsyncMock:
        captured.append(
            {"url": url, "json": kwargs.get("json"), "headers": kwargs.get("headers")}
        )
        mock_response = AsyncMock()
        mock_response.status_code = 200
        return mock_response

    with patch("order_processor.webhook.httpx.AsyncClient") as mock_client_class:
        mock_instance = AsyncMock()
        mock_instance.post = mock_post
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_instance

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
            status=OrderStatus.PROCESSING, priority=4
        )

        await deliver_webhook(tenant, order)

    assert len(captured) == 1
    payload = captured[0]["json"]
    assert payload["order_id"] == 1
    assert payload["status"] == "processing"

    expected_sig = hmac.new(
        api_key.encode(),
        json.dumps(payload).encode(),
        hashlib.sha256,
    ).hexdigest()
    assert captured[0]["headers"]["X-Signature"] == expected_sig
