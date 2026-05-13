from datetime import datetime
from models.tenant import Tenant
from schemas.order import OrderCreate, OrderResponse, OrderResponseList
from models.order_status import OrderStatus
from models.order import Order
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_


async def create_order(
    tenant_id: int, order: OrderCreate, db: AsyncSession
) -> OrderResponse:
    curr_tenant = await db.get(Tenant, tenant_id)

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

    db.add(result)
    await db.flush()
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

    stmt = select(Order).where(Order.tenant_id == tenant_id).order_by(Order.created_at, Order.id)

    if status is not None:
        stmt = stmt.where(Order.status == status)

    # Offset pagination
    if cursor_id is None:
        offset = (page - 1) * limit
        stmt = stmt.offset(offset).limit(limit)
        response = (await db.execute(stmt)).scalars().all()
    # Cursor pagination which takes precedence since it is more performant and consistent than offset pagination,
    # where it's possible to have duplicate or missing items across pages if there are new orders
    # being created while paginating
    else:
        stmt = stmt.where(or_(cursor_created_at < Order.created_at,and_( Order.created_at == cursor_created_at, cursor_id < Order.id))).limit(limit)
        response = (await db.execute(stmt)).scalars().all()


    next_cursor = response[-1].id if (response and len(response) == limit) else None
    next_cursor_created_at = response[-1].created_at if (response and len(response) == limit) else None

    return OrderResponseList(
        orders=[OrderResponse.model_validate(order) for order in response],
        next_cursor=next_cursor,
        next_cursor_created_at=next_cursor_created_at,
    )
