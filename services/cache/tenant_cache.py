import json

from redis.asyncio import Redis


async def check_cache(api_key: str, redis: Redis) -> dict | None:
    key = f"tenant:{api_key}:config"
    cache = await redis.get(key)
    if cache:
        return json.loads(cache)
    return None


async def cache_with_TTL(ttl: int, api_key: str, value: dict, redis: Redis) -> None:
    key = f"tenant:{api_key}:config"
    value = json.dumps(value)
    await redis.setex(key, ttl, value)


async def invalidate_cache_on_update(api_key: str, redis: Redis) -> None:
    key = f"tenant:{api_key}:config"
    await redis.delete(key)
