from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.order import Order
from models.order_status import OrderStatus


async def test_create_order(
    client: AsyncClient, db_session: AsyncSession, tenant_credentials: tuple[str, int]
) -> None:
    api_key, tena_id = tenant_credentials
    order_response = await client.post(
        f"/tenants/{tena_id}/orders/",
        json={"price": 50.0},
        headers={"api-key": api_key},
    )

    record = await db_session.get(Order, order_response.json()["id"])
    assert record is not None
    assert record.price == 50.0
    assert record.status == OrderStatus.PENDING
    assert record.priority == 4
    assert record.created_at is not None
