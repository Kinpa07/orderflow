from collections.abc import Callable

from httpx import AsyncClient
from redis.asyncio import Redis

from schemas.order import OrderCreate


async def test_order_creation_publishes_to_stream(
    client: AsyncClient,
    redis_client: Redis,
    tenant_credentials: tuple[str, int],
    make_order: Callable[..., OrderCreate],
) -> None:
    api_key, tenant_id = tenant_credentials

    response = await client.post(
        f"/tenants/{tenant_id}/orders/",
        json=make_order().model_dump(),
        headers={"api-key": api_key},
    )
    order_id = response.json()["id"]

    messages = await redis_client.xrange("orders", "-", "+")
    assert len(messages) == 1
    _, fields = messages[0]
    assert fields["order_id"] == str(order_id)
    assert fields["tenant_id"] == str(tenant_id)
