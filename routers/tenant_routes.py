from fastapi import APIRouter, Depends, HTTPException
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies.auth import verify_api_key
from dependencies.db import get_db
from dependencies.rate_limit import rate_limit
from dependencies.redis import get_redis
from repositories.tenant_repository import list_dead_letters
from schemas.tenant import (
    DeadLetterWebhookListResponse,
    DeadLetterWebhookResponse,
    TenantCreate,
    TenantResponse,
    TenantUpdate,
)
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
    tenant: TenantResponse = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    _: bool = Depends(rate_limit),
) -> TenantResponse:

    if tenant.id != tenant_id:
        raise HTTPException(status_code=403, detail="Forbidden: Tenant ID mismatch")

    result = await modify_tenant(tenant, update, db, redis)
    return result


@tenant_router.get(
    "/{tenant_id}/webhooks/dead-letter",
    response_model=DeadLetterWebhookListResponse,
)
async def list_dead_letter_webhooks(
    tenant_id: int,
    db: AsyncSession = Depends(get_db),
    tenant: TenantResponse = Depends(verify_api_key),
    _: bool = Depends(rate_limit),
) -> DeadLetterWebhookListResponse:
    if tenant.id != tenant_id:
        raise HTTPException(status_code=403, detail="Forbidden: Tenant ID mismatch")

    records = await list_dead_letters(tenant_id, db)
    return DeadLetterWebhookListResponse(
        items=[DeadLetterWebhookResponse.model_validate(r) for r in records],
        total=len(records),
    )
