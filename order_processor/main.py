import asyncio
from asyncio import create_task
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.exceptions import ResponseError

from db.session import AsyncSessionLocal
from models.order_status import OrderStatus
from models.tenant import Tenant  # noqa: F401
from order_processor.redis import redis_client
from order_processor.webhook import deliver_webhook
from repositories.order_repository import add_order_history, fetch_order
from repositories.tenant_repository import get_tenant


async def consume_orders() -> None:
    while True:
        messages = await redis_client.xreadgroup(
            "processing-group",
            "order-processor",
            {"orders": ">"},
            count=1,
            block=0,
        )
        for stream in messages:
            for message in stream[1]:
                async with AsyncSessionLocal() as session:
                    order = await fetch_order(
                        int(message[1]["tenant_id"]),
                        int(message[1]["order_id"]),
                        session,
                    )
                    tenant = await get_tenant(int(message[1]["tenant_id"]), session)

                    if order is None or tenant is None:
                        await redis_client.xack(
                            "orders", "processing-group", message[0]
                        )
                        continue

                    order.status = OrderStatus.PROCESSING
                    await add_order_history(order, session)
                    await session.flush()
                    await session.commit()

                    if tenant.webhook_url:
                        await deliver_webhook(tenant, order)

                    await asyncio.sleep(1)

                    await session.refresh(order)

                    order.status = OrderStatus.SHIPPED
                    await add_order_history(order, session)
                    await session.flush()
                    await session.commit()

                    if tenant.webhook_url:
                        await deliver_webhook(tenant, order)

                    await redis_client.xack("orders", "processing-group", message[0])


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    try:
        # runs at startup
        await redis_client.xgroup_create(
            "orders", "processing-group", id="0", mkstream=True
        )
    except ResponseError:
        pass

    create_task(consume_orders())
    yield
    # runs at shutdown


app = FastAPI(
    lifespan=lifespan,
)
