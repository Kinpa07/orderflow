import asyncio
import hashlib
import hmac
import json
from datetime import UTC, datetime

import httpx

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

    signature = hmac.new(
        key=tenant.api_key.encode(),
        msg=json.dumps(body).encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()

    last_error = "unknown error"
    for attempt in range(3):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    tenant.webhook_url,
                    json=body,
                    headers={"X-Signature": signature},
                    timeout=5,
                )
                if response.status_code < 400:
                    return
                last_error = f"HTTP {response.status_code}"

        except httpx.HTTPError as e:
            last_error = str(e)

        await asyncio.sleep(2**attempt)

    async with AsyncSessionLocal() as session:
        session.add(DeadLetterWebhook(
            tenant_id=tenant.id,
            order_id=order.id,
            webhook_url=tenant.webhook_url,
            payload=json.dumps(body),
            error_message=last_error,
        ))
        await session.commit()
