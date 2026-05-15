from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.order import Order
from models.order_status import OrderStatus
from models.order_status_history import OrderStatusHistory


async def test_create_order(
    client: AsyncClient, db_session: AsyncSession, tenant_credentials: tuple[str, int]
) -> None:
    api_key, tena_id = tenant_credentials
    order_response = await client.post(
        f"/tenants/{tena_id}/orders/",
        json={"price": 50.0},
        headers={"api-key": api_key},
    )
    assert order_response.status_code == 200
    record = await db_session.get(Order, order_response.json()["id"])
    assert record is not None
    assert record.price == 50.0
    assert record.status == OrderStatus.PENDING
    assert record.priority == 4
    assert record.created_at is not None

    stmt = select(OrderStatusHistory).where(OrderStatusHistory.order_id == record.id)
    history_record = (await db_session.execute(stmt)).scalars().first()
    assert history_record is not None
    assert history_record.status == OrderStatus.PENDING
    assert history_record.order_id == order_response.json()["id"]
