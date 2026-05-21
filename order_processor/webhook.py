import asyncio
import hashlib
import hmac
import json
from datetime import UTC, datetime
from time import perf_counter

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from config import WEBHOOK_RETRY_COUNT, WEBHOOK_TIMEOUT
from db.session import AsyncSessionLocal
from metrics import (
    dead_letter_queue_depth,
    webhook_deliveries_total,
    webhook_delivery_duration_seconds,
)
from models.dead_letter_webhook import DeadLetterWebhook
from models.order import Order
from models.tenant import Tenant

logger = get_logger()


async def refresh_dead_letter_depth(session: AsyncSession) -> None:
    count = await session.scalar(
        select(func.count()).select_from(DeadLetterWebhook)
    )
    dead_letter_queue_depth.set(count or 0)


async def deliver_webhook(tenant: Tenant, order: Order, request_id: str) -> None:
    if not tenant.webhook_url:
        return
    body = {
        "order_id": order.id,
        "tenant_id": order.tenant_id,
        "price": order.price,
        "status": order.status.value,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    payload = json.dumps(body, separators=(",", ":")).encode()

    signature = hmac.new(
        key=tenant.api_key.encode(),
        msg=payload,
        digestmod=hashlib.sha256,
    ).hexdigest()

    start = perf_counter()
    last_error = "unknown error"
    for attempt in range(WEBHOOK_RETRY_COUNT):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    tenant.webhook_url,
                    content=payload,
                    headers={
                        "X-Signature": signature,
                        "X-Request-Id": request_id,
                        "Content-Type": "application/json",
                    },
                    timeout=WEBHOOK_TIMEOUT,
                )
                if response.status_code < 400:
                    webhook_delivery_duration_seconds.observe(perf_counter() - start)
                    webhook_deliveries_total.labels(status="success").inc()
                    return
                last_error = f"HTTP {response.status_code}"

        except httpx.HTTPError as e:
            last_error = str(e)

        await asyncio.sleep(2**attempt)

    webhook_delivery_duration_seconds.observe(perf_counter() - start)
    webhook_deliveries_total.labels(status="dead_letter").inc()

    async with AsyncSessionLocal() as session:
        session.add(
            DeadLetterWebhook(
                tenant_id=tenant.id,
                order_id=order.id,
                webhook_url=tenant.webhook_url,
                payload=json.dumps(body),
                error_message=last_error,
            )
        )
        await session.commit()
        await refresh_dead_letter_depth(session)


async def safe_deliver_webhook(tenant: Tenant, order: Order, request_id: str) -> None:
    try:
        await deliver_webhook(tenant, order, request_id)
    except Exception:
        logger.exception(
            "webhook delivery raised",
            tenant_id=tenant.id,
            order_id=order.id,
        )
