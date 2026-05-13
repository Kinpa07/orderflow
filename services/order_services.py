from datetime import datetime
from schemas.order import OrderCreate, OrderResponse, OrderResponseList
from models.order_status import OrderStatus
from models.order import Order
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.order_repository import add_order, display_orders, add_order_history
from repositories.tenant_repository import get_tenant


async def create_order(
    tenant_id: int, order: OrderCreate, db: AsyncSession
) -> OrderResponse:

    curr_tenant = await get_tenant(tenant_id, db)

    if not curr_tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    if (
        curr_tenant.config is not None
        and curr_tenant.config.get("maximum_price") is not None
        and order.price > curr_tenant.config["maximum_price"]
    ):
        raise HTTPException(
            status_code=400,
            detail=f"Price exceeds maximum allowed price of {curr_tenant.config['maximum_price']}",
        )

    result = Order(
        tenant_id=tenant_id,
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

    response = await display_orders(
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
