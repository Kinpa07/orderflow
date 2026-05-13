from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient

from models.order import Order
from models.order_status import OrderStatus
from models.order_status_history import OrderStatusHistory
from sqlalchemy import select




async def create_tenant_to_get_api_key(client: AsyncClient) -> tuple[str, int]:
    tenant_response = await client.post(
        "/tenants/",
        json={
            "company_name": "Test Company",
            "contact_name": "John Doe",
            "email": "john.doe@testcompany.com",
            "phone": "1234567890",
            "config": {"maximum_price": 100.0},
        },
    )
    api_key = tenant_response.json()["api_key"]
    id = tenant_response.json()["id"]
    return api_key, id

async def test_create_order(client: AsyncClient, db_session: AsyncSession) -> None:
    api_key, tena_id = await create_tenant_to_get_api_key(client)
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

    history_record = select(OrderStatusHistory).where(
        OrderStatusHistory.order_id == record.id
    )
    history_record = (await db_session.execute(history_record)).scalars().first()
    assert history_record is not None
    assert history_record.status == OrderStatus.PENDING
    assert history_record.order_id == order_response.json()["id"]