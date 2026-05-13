from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from datetime import datetime
from models.order_status import OrderStatus
from models.order import Order


async def add_order(order: Order, db: AsyncSession) -> Order:
    db.add(order)
    await db.flush()
    return order


async def display_orders(
    tenant_id: int,
    db: AsyncSession,
    status: OrderStatus | None = None,
    cursor_created_at: datetime | None = None,
    cursor_id: int | None = None,
    page: int = 1,
    limit: int = 20,
) -> list[Order]:
    stmt = (
        select(Order)
        .where(Order.tenant_id == tenant_id)
        .order_by(Order.created_at, Order.id)
    )

    if status is not None:
        stmt = stmt.where(Order.status == status)

    if cursor_id is None:
        offset = (page - 1) * limit
        stmt = stmt.offset(offset).limit(limit)
        response = (await db.execute(stmt)).scalars().all()

    else:
        stmt = stmt.where(
            or_(
                cursor_created_at < Order.created_at,
                and_(Order.created_at == cursor_created_at, cursor_id < Order.id),
            )
        ).limit(limit)
        response = (await db.execute(stmt)).scalars().all()

    return response
