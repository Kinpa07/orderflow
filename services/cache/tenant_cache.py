import json
from typing import Any

from redis.asyncio import Redis


async def check_cache(api_key: str, redis: Redis) -> dict[str, Any] | None:
    key = f"tenant:{api_key}:config"
    cache = await redis.get(key)
    if cache:
        return dict(json.loads(cache))
    return None


async def cache_with_ttl(
    ttl: int, api_key: str, value: dict[str, Any], redis: Redis
) -> None:
    key = f"tenant:{api_key}:config"
    serialized = json.dumps(value)
    await redis.setex(key, ttl, serialized)


async def invalidate_cache_on_update(api_key: str, redis: Redis) -> None:
    key = f"tenant:{api_key}:config"
    await redis.delete(key)
