import uuid

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from models.tenant import Tenant
from repositories.tenant_repository import add_tenant, get_tenant, update_tenant
from schemas.tenant import TenantCreate, TenantResponse, TenantUpdate
from services.cache.tenant_cache import invalidate_cache_on_update


async def create_tenant(tenant: TenantCreate, db: AsyncSession) -> TenantResponse:
    result = Tenant(**tenant.model_dump(), api_key=uuid.uuid4().hex)
    await add_tenant(result, db)
    return TenantResponse.model_validate(result)


async def modify_tenant(
    tenant: TenantResponse, update: TenantUpdate, db: AsyncSession, redis: Redis
) -> TenantResponse:

    refreshed = await get_tenant(tenant.id, db)
    if refreshed is None:
        raise ValueError(f"Tenant {tenant.id} not found")

    update_dict = update.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(refreshed, key, value)

    result = await update_tenant(refreshed, db)
    await invalidate_cache_on_update(refreshed.api_key, redis)

    return TenantResponse.model_validate(result)
