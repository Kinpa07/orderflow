from fastapi import APIRouter, Depends, HTTPException
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies.auth import verify_api_key
from dependencies.db import get_db
from dependencies.rate_limit import rate_limit
from dependencies.redis import get_redis
from models.tenant import Tenant
from schemas.tenant import TenantCreate, TenantResponse, TenantUpdate
from services.tenant_services import create_tenant, modify_tenant

tenant_router = APIRouter()


@tenant_router.post("/", response_model=TenantResponse)
async def create_tenants(
    tenant: TenantCreate, db: AsyncSession = Depends(get_db)
) -> TenantResponse:
    response = await create_tenant(tenant, db)
    return response


@tenant_router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenants(
    tenant_id: int,
    update: TenantUpdate,
    tenant: Tenant = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    _: bool = Depends(rate_limit),
) -> TenantResponse:

    if tenant.id != tenant_id:
        raise HTTPException(status_code=403, detail="Forbidden: Tenant ID mismatch")

    result = await modify_tenant(tenant, update, db, redis)
    return result
