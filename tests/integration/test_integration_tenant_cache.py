import json
from collections.abc import Callable

from httpx import AsyncClient
from redis.asyncio import Redis

from schemas.order import OrderCreate


async def test_tenant_config_cached_after_first_request(
    client: AsyncClient,
    redis_client: Redis,
    tenant_credentials: tuple[str, int],
    make_order: Callable[..., OrderCreate],
) -> None:
    api_key, tenant_id = tenant_credentials

    await client.post(
        f"/tenants/{tenant_id}/orders/",
        json=make_order().model_dump(),
        headers={"api-key": api_key},
    )

    cache_key = f"tenant:{api_key}:config"
    cached = await redis_client.get(cache_key)
    assert cached is not None

    data = json.loads(cached)
    assert data["id"] == tenant_id
    assert data["api_key"] == api_key
