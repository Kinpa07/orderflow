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
    tenant: Tenant, update: TenantUpdate, db: AsyncSession, redis: Redis
) -> TenantResponse:

    tenant = await get_tenant(tenant.id, db)

    update_dict = update.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(tenant, key, value)

    result = await update_tenant(tenant, db)
    await invalidate_cache_on_update(tenant.api_key, redis)

    return TenantResponse.model_validate(result)
