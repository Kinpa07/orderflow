from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.order_status import OrderStatus
from models.order_status_history import OrderStatusHistory


async def test_create_order_status_history(
    db_session: AsyncSession,
    order_id: int,
) -> None:

    stmt = select(OrderStatusHistory).where(OrderStatusHistory.order_id == order_id)
    history_record = (await db_session.execute(stmt)).scalars().first()
    assert history_record is not None
    assert history_record.status == OrderStatus.PENDING
    assert history_record.order_id == order_id
