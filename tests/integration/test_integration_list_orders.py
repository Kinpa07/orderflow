from datetime import datetime

from httpx import AsyncClient
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.order import Order
from models.order_status import OrderStatus
from tests.conftest import make_orders


async def test_list_orders(
    client: AsyncClient, db_session: AsyncSession, tenant_credentials: tuple[str, int]
) -> None:

    await make_orders(client, tenant_credentials)

    api_key, tenant_id = tenant_credentials
    orders_response = await client.get(
        f"/tenants/{tenant_id}/orders/",
        headers={"api-key": api_key},
        params={
            "page": 1,
            "limit": 20,
        },
    )

    db_orders = (
        select(Order)
        .where(Order.tenant_id == tenant_id)
        .order_by(Order.created_at, Order.id)
        .limit(20)
    )
    db_orders = (await db_session.execute(db_orders)).scalars().all()

    assert len(db_orders) == len(orders_response.json()["orders"])
    assert orders_response.json()["next_cursor"] is not None
    assert orders_response.json()["next_cursor_created_at"] is not None

    for db_order, order in zip(db_orders, orders_response.json()["orders"]):
        assert db_order.id == order["id"]
        assert db_order.price == order["price"]
        assert db_order.status == OrderStatus(order["status"])
        assert db_order.priority == order["priority"]
        assert db_order.created_at == datetime.fromisoformat(order["created_at"])


async def test_list_orders_with_status(
    client: AsyncClient, db_session: AsyncSession, tenant_credentials: tuple[str, int]
) -> None:

    await make_orders(client, tenant_credentials)
    api_key, tenant_id = tenant_credentials

    stmt = (
        select(Order)
        .where(Order.tenant_id == tenant_id)
        .order_by(Order.created_at, Order.id)
        .limit(20)
    )

    db_orders = (await db_session.execute(stmt)).scalars().all()

    count = 0
    for order in db_orders:
        if order.id % 2 == 0:
            order.status = OrderStatus.SHIPPED
            count += 1

    await db_session.flush()

    await db_session.commit()

    orders_response = await client.get(
        f"/tenants/{tenant_id}/orders/",
        headers={"api-key": api_key},
        params={
            "page": 1,
            "limit": 21,
            "status": OrderStatus.SHIPPED.value,
        },
    )

    print(orders_response.json())
    assert count == len(orders_response.json()["orders"])
    assert orders_response.json()["next_cursor"] is None
    assert orders_response.json()["next_cursor_created_at"] is None
    assert all(
        OrderStatus(order["status"]) == OrderStatus.SHIPPED
        for order in orders_response.json()["orders"]
    )


async def test_list_orders_with_cursor(
    client: AsyncClient, tenant_credentials: tuple[str, int]
) -> None:
    await make_orders(client, tenant_credentials)
    api_key, tenant_id = tenant_credentials

    get_cursor_response = await client.get(
        f"/tenants/{tenant_id}/orders/",
        headers={"api-key": api_key},
        params={
            "page": 1,
            "limit": 10,
        },
    )

    next_cursor = get_cursor_response.json()["next_cursor"]
    next_cursor_created_at = get_cursor_response.json()["next_cursor_created_at"]

    orders_response = await client.get(
        f"/tenants/{tenant_id}/orders/",
        headers={"api-key": api_key},
        params={
            "page": 1,
            "limit": 20,
            "cursor_id": next_cursor,
            "cursor_created_at": next_cursor_created_at,
        },
    )

    assert len(orders_response.json()["orders"]) == 11
    assert all(
        order["id"] > next_cursor
        for order in orders_response.json()["orders"]
    )
