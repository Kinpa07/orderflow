import asyncio
from asyncio import create_task
from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.exceptions import ResponseError

from db.session import AsyncSessionLocal
from models.order_status import OrderStatus
from models.tenant import Tenant  # noqa: F401
from order_processor.redis import redis_client
from repositories.order_repository import fetch_order


async def consume_orders():
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
                    setattr(order, "status", OrderStatus.PROCESSING)
                    await session.flush()
                    await session.commit()

                    await asyncio.sleep(1)

                    await session.refresh(order)

                    setattr(order, "status", OrderStatus.SHIPPED)
                    await session.flush()
                    await session.commit()

                    await redis_client.xack("orders", "processing-group", message[0])


@asynccontextmanager
async def lifespan(app: FastAPI):
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
