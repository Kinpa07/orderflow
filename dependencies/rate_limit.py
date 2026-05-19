from fastapi import Depends, HTTPException
from redis.asyncio import Redis

from dependencies.auth import verify_api_key
from dependencies.redis import get_redis
from models.tenant import Tenant
from services.cache.rate_limit import check_rate_limit

RATE_LIMIT = 10


async def rate_limit(
    tenant: Tenant = Depends(verify_api_key),
    redis: Redis = Depends(get_redis),
) -> bool:
    count = await check_rate_limit(tenant.api_key, redis)

    if count > RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    return True
