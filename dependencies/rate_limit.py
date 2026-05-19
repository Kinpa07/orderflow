import os

from fastapi import Depends, HTTPException
from redis.asyncio import Redis

from dependencies.auth import verify_api_key
from dependencies.redis import get_redis
from schemas.tenant import TenantResponse
from services.cache.rate_limit import check_rate_limit

RATE_LIMIT = int(os.environ.get("RATE_LIMIT", "15"))


async def rate_limit(
    tenant: TenantResponse = Depends(verify_api_key),
    redis: Redis = Depends(get_redis),
) -> bool:
    count = await check_rate_limit(tenant.api_key, redis)

    if count > RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    return True
