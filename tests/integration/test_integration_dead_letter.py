from collections.abc import Callable

from httpx import AsyncClient
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.dead_letter_webhook import DeadLetterWebhook
from models.order_status import OrderStatus
from models.tenant import Tenant
from schemas.order import OrderCreate
from schemas.tenant import TenantCreate


async def test_failed_webhook_stored_in_dead_letter(
    client: AsyncClient,
    redis_client: Redis,
    make_tenant: Callable[..., TenantCreate],
    make_order: Callable[..., OrderCreate],
    db_session: AsyncSession,
) -> None:
    from models.order import Order
    from order_processor.webhook import deliver_webhook

    tenant_response = await client.post(
        "/tenants/",
        json=make_tenant(webhook_url="http://localhost:9999/dead").model_dump(),
    )
    api_key = tenant_response.json()["api_key"]
    tenant_id = tenant_response.json()["id"]

    order_response = await client.post(
        f"/tenants/{tenant_id}/orders/",
        json=make_order().model_dump(),
        headers={"api-key": api_key},
    )
    order_id = order_response.json()["id"]

    tenant = Tenant(
        id=tenant_id,
        company_name="Test",
        contact_name="Test",
        email="test@test.com",
        phone="123",
        config={},
        api_key=api_key,
        webhook_url="http://localhost:9999/dead",
    )
    order = Order(
        id=order_id, tenant_id=tenant_id, price=50.0,
        status=OrderStatus.SHIPPED, priority=4
    )

    await deliver_webhook(tenant, order, "test-request-id")

    result = await db_session.execute(
        select(DeadLetterWebhook).where(DeadLetterWebhook.tenant_id == tenant_id)
    )
    records = result.scalars().all()
    assert len(records) >= 1
    assert records[0].order_id == order_id
    assert records[0].webhook_url == "http://localhost:9999/dead"
    assert records[0].error_message != ""
