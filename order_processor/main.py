import asyncio
from collections.abc import AsyncIterator, Coroutine
from contextlib import asynccontextmanager
from time import perf_counter
from typing import Any

import structlog
import structlog.contextvars
from fastapi import FastAPI
from prometheus_client import make_asgi_app
from redis.exceptions import ResponseError
from structlog import get_logger

from clients.redis import redis_client
from db.session import AsyncSessionLocal
from metrics import order_processing_duration_seconds
from models.order_status import OrderStatus
from models.tenant import Tenant  # noqa: F401
from order_processor.webhook import refresh_dead_letter_depth, safe_deliver_webhook
from repositories.order_repository import add_order_history, fetch_order
from repositories.tenant_repository import get_tenant

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
)

logger = get_logger()

_background_tasks: set[asyncio.Task[None]] = set()


def spawn_background(coro: Coroutine[Any, Any, None]) -> asyncio.Task[None]:
    task = asyncio.create_task(coro)
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return task


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
                start = perf_counter()
                try:
                    request_id = message[1].get("request_id", "unknown")
                    tenant_id = int(message[1]["tenant_id"])
                    order_id = int(message[1]["order_id"])
                    structlog.contextvars.clear_contextvars()
                    structlog.contextvars.bind_contextvars(request_id=request_id)

                    async with AsyncSessionLocal() as session:
                        order = await fetch_order(tenant_id, order_id, session)
                        tenant = await get_tenant(tenant_id, session)

                        if order is None or tenant is None:
                            await redis_client.xack(
                                "orders", "processing-group", message[0]
                            )
                            continue

                        order.status = OrderStatus.PROCESSING
                        await add_order_history(order, session)
                        await session.commit()
                        logger.info(
                            "Order status updated",
                            order_id=order.id,
                            status=order.status.value,
                        )

                    if tenant.webhook_url:
                        spawn_background(
                            safe_deliver_webhook(tenant, order, request_id)
                        )

                    await asyncio.sleep(1)

                    async with AsyncSessionLocal() as session:
                        order = await fetch_order(tenant_id, order_id, session)
                        if order is None:
                            await redis_client.xack(
                                "orders", "processing-group", message[0]
                            )
                            continue

                        order.status = OrderStatus.SHIPPED
                        await add_order_history(order, session)
                        await session.commit()
                        logger.info(
                            "Order status updated",
                            order_id=order.id,
                            status=order.status.value,
                        )

                    if tenant.webhook_url:
                        spawn_background(
                            safe_deliver_webhook(tenant, order, request_id)
                        )

                    await redis_client.xack(
                        "orders", "processing-group", message[0]
                    )
                except Exception:
                    logger.exception(
                        "order processing failed",
                        stream_id=message[0],
                    )
                finally:
                    order_processing_duration_seconds.observe(
                        perf_counter() - start
                    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    try:
        await redis_client.xgroup_create(
            "orders", "processing-group", id="0", mkstream=True
        )
    except ResponseError:
        pass

    async with AsyncSessionLocal() as session:
        await refresh_dead_letter_depth(session)

    spawn_background(consume_orders())
    yield


app = FastAPI(
    lifespan=lifespan,
)
app.mount("/metrics", make_asgi_app())
