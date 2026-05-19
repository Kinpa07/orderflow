from fastapi import Depends, Header, HTTPException, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from config import TENANT_CACHE_TTL
from dependencies.db import get_db
from dependencies.redis import get_redis
from repositories.tenant_repository import get_tenant_by_api_key
from schemas.tenant import TenantResponse
from services.cache.tenant_cache import (
    cache_with_ttl,
    check_cache,
)


async def verify_api_key(
    request: Request,
    api_key: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> TenantResponse:

    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")

    cache = await check_cache(api_key, redis)
    if cache:
        tenant = TenantResponse(**cache)
    else:
        db_tenant = await get_tenant_by_api_key(api_key, db)
        if not db_tenant:
            raise HTTPException(status_code=401, detail="Invalid API key")
        tenant = TenantResponse.model_validate(db_tenant)
        await cache_with_ttl(
            TENANT_CACHE_TTL, api_key, tenant.model_dump(mode="json"), redis
        )

    request.state.tenant_id = tenant.id
    return tenant
