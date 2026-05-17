from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from models.order import Order
from models.order_status import OrderStatus
from models.tenant import Tenant
from repositories.order_repository import (
    add_order,
    add_order_history,
    fetch_order,
    list_orders,
)
from schemas.order import OrderCreate, OrderResponse, OrderResponseList


async def create_order(
    tenant: Tenant, order: OrderCreate, db: AsyncSession
) -> OrderResponse:

    maximum_price = tenant.config.get("maximum_price")

    if maximum_price is not None and order.price > maximum_price:
        raise HTTPException(
            status_code=400,
            detail=f"Price exceeds maximum allowed price of {maximum_price}",
        )

    result = Order(
        tenant_id=tenant.id,
        price=order.price,
    )

    await add_order(result, db)
    await add_order_history(result, db)
    return OrderResponse.model_validate(result)


async def list_order(
    tenant_id: int,
    db: AsyncSession,
    page: int = 1,
    cursor_created_at: datetime | None = None,
    cursor_id: int | None = None,
    status: OrderStatus | None = None,
    limit: int = 20,
) -> OrderResponseList:

    response = await list_orders(
        tenant_id, db, status, cursor_created_at, cursor_id, page, limit
    )

    next_cursor = response[-1].id if (response and len(response) == limit) else None
    next_cursor_created_at = (
        response[-1].created_at if (response and len(response) == limit) else None
    )

    return OrderResponseList(
        orders=[OrderResponse.model_validate(order) for order in response],
        next_cursor=next_cursor,
        next_cursor_created_at=next_cursor_created_at,
    )


async def get_order(tenant_id: int, order_id: int, db: AsyncSession) -> OrderResponse:

    response = await fetch_order(tenant_id, order_id, db)

    if not response:
        raise HTTPException(status_code=404, detail="Order not found")

    return OrderResponse.model_validate(response)
