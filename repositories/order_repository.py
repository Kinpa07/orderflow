from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from datetime import datetime
from models.order_status import OrderStatus
from models.order import Order
from models.order_status_history import OrderStatusHistory


async def add_order(order: Order, db: AsyncSession) -> Order:
    db.add(order)
    await db.flush()
    return order


async def add_order_history(order: Order, db: AsyncSession) -> None:
    history = OrderStatusHistory(order_id=order.id, status=order.status)
    db.add(history)
    await db.flush()


async def list_orders(
    tenant_id: int,
    db: AsyncSession,
    status: OrderStatus | None = None,
    cursor_created_at: datetime | None = None,
    cursor_id: int | None = None,
    page: int = 1,
    limit: int = 20,
) -> Sequence[Order]:
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


async def fetch_order(tenant_id: int, order_id: int, db: AsyncSession) -> Order | None:
    stmt = select(Order).where(and_(Order.tenant_id == tenant_id, Order.id == order_id))
    response = (await db.execute(stmt)).scalars().first()
    return response
