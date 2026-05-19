from fastapi import Depends, Header, HTTPException, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies.db import get_db
from dependencies.redis import get_redis
from models.tenant import Tenant
from repositories.tenant_repository import get_tenant_by_api_key
from services.cache.tenant_cache import (
    cache_with_TTL,
    check_cache,
)


async def verify_api_key(
    request: Request,
    api_key: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> Tenant:

    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")

    cache = await check_cache(api_key, redis)
    if cache:
        cache_as_obj = Tenant(**cache)
        request.state.tenant_id = cache_as_obj.id
        return cache_as_obj
    else:
        tenant = await get_tenant_by_api_key(api_key, db)
        if not tenant:
            raise HTTPException(status_code=401, detail="Invalid API key")
        await cache_with_TTL(
            60,
            api_key,
            {
                "id": tenant.id,
                "company_name": tenant.company_name,
                "contact_name": tenant.contact_name,
                "email": tenant.email,
                "phone": tenant.phone,
                "config": tenant.config,
                "api_key": tenant.api_key,
            },
            redis,
        )

    request.state.tenant_id = tenant.id
    return tenant
