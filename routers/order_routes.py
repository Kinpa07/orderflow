from fastapi import APIRouter, Depends, HTTPException
from models.tenant import Tenant
from schemas.order import OrderResponse, OrderCreate, OrderResponseList
from models.order_status import OrderStatus
from datetime import datetime
from services.order_services import create_order, list_order, get_order
from dependencies.auth import verify_api_key
from dependencies.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession

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
    tenant: Tenant = Depends(verify_api_key),
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
    tenant: Tenant = Depends(verify_api_key),
) -> OrderResponse:
    if tenant.id != tenant_id:
        raise HTTPException(status_code=403, detail="Forbidden: Tenant ID mismatch")
    response = await get_order(tenant_id, order_id, db)
    return response


@order_router.post("/", response_model=OrderResponse)
async def create_orders(
    tenant_id: int,
    order: OrderCreate,
    tenant: Tenant = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
) -> OrderResponse:
    if tenant.id != tenant_id:
        raise HTTPException(status_code=403, detail="Forbidden: Tenant ID mismatch")
    response = await create_order(tenant_id, order, db)
    return response
