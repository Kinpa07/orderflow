from datetime import datetime

from redis.asyncio import Redis


async def check_rate_limit(
    api_key: str,
    redis: Redis,
    ttl: int = 60,
) -> int:
    key = f"tenant:{api_key}:rate_limit:{datetime.now().strftime('%Y%m%d%H%M')}"
    count = int(await redis.incr(key))
    if count == 1:
        await redis.expire(key, ttl)
    return count
