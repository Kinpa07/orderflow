import asyncio
import hashlib
import hmac
import json
from datetime import UTC, datetime

import httpx

from config import WEBHOOK_RETRY_COUNT, WEBHOOK_TIMEOUT
from db.session import AsyncSessionLocal
from models.dead_letter_webhook import DeadLetterWebhook
from models.order import Order
from models.tenant import Tenant


async def deliver_webhook(tenant: Tenant, order: Order) -> None:
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

    last_error = "unknown error"
    for attempt in range(WEBHOOK_RETRY_COUNT):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    tenant.webhook_url,
                    content=payload,
                    headers={
                        "X-Signature": signature,
                        "Content-Type": "application/json",
                    },
                    timeout=WEBHOOK_TIMEOUT,
                )
                if response.status_code < 400:
                    return
                last_error = f"HTTP {response.status_code}"

        except httpx.HTTPError as e:
            last_error = str(e)

        await asyncio.sleep(2**attempt)

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
