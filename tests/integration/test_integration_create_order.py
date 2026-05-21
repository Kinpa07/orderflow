from collections.abc import Callable

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.order import Order
from models.order_status import OrderStatus
from models.order_status_history import OrderStatusHistory
from schemas.order import OrderCreate


async def test_create_order(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_credentials: tuple[str, int],
    make_order: Callable[..., OrderCreate],
) -> None:
    api_key, tena_id = tenant_credentials
    order_response = await client.post(
        f"/tenants/{tena_id}/orders/",
        json=make_order().model_dump(),
        headers={"api-key": api_key},
    )

    record = await db_session.get(Order, order_response.json()["id"])
    assert record is not None
    assert record.price == 50.0
    assert record.priority == 4
    assert record.created_at is not None

    initial_history = (
        await db_session.execute(
            select(OrderStatusHistory)
            .where(OrderStatusHistory.order_id == record.id)
            .order_by(OrderStatusHistory.id)
        )
    ).scalars().first()
    assert initial_history is not None
    assert initial_history.status == OrderStatus.PENDING
