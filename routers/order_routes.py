from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies.auth import verify_api_key
from dependencies.db import get_db
from dependencies.rate_limit import rate_limit
from dependencies.redis import get_redis
from models.order_status import OrderStatus
from schemas.tenant import TenantResponse
from schemas.order import OrderCreate, OrderResponse, OrderResponseList
from services.order_services import create_order, get_order, list_order

order_router = APIRouter()


@order_router.get("/", response_model=OrderResponseList)
async def list_orders(
    tenant_id: int,
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    cursor_created_at: datetime | None = None,
    cursor_id: int | None = None,
    status: OrderStatus | None = None,
    limit: int = 20,
    tenant: TenantResponse = Depends(verify_api_key),
    _: bool = Depends(rate_limit),
) -> OrderResponseList:
    if tenant.id != tenant_id:
        raise HTTPException(status_code=403, detail="Forbidden: Tenant ID mismatch")
    response = await list_order(
        tenant_id,
        db,
        page,
        cursor_created_at,
        cursor_id,
        status,
        limit,
    )
    return response


@order_router.get("/{order_id}", response_model=OrderResponse)
async def get_order_status(
    tenant_id: int,
    order_id: int,
    db: AsyncSession = Depends(get_db),
    tenant: TenantResponse = Depends(verify_api_key),
    _: bool = Depends(rate_limit),
) -> OrderResponse:
    if tenant.id != tenant_id:
        raise HTTPException(status_code=403, detail="Forbidden: Tenant ID mismatch")
    response = await get_order(tenant_id, order_id, db)
    return response


@order_router.post("/", response_model=OrderResponse)
async def create_orders(
    tenant_id: int,
    order: OrderCreate,
    tenant: TenantResponse = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(rate_limit),
    redis: Redis = Depends(get_redis),
) -> OrderResponse:
    if tenant.id != tenant_id:
        raise HTTPException(status_code=403, detail="Forbidden: Tenant ID mismatch")
    response = await create_order(tenant, order, db, redis)
    return response
