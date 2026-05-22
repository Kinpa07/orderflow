from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.dead_letter_webhook import DeadLetterWebhook
from models.tenant import Tenant


async def get_tenant(tenant_id: int, db: AsyncSession) -> Tenant | None:
    return await db.get(Tenant, tenant_id)


async def get_tenant_by_api_key(api_key: str, db: AsyncSession) -> Tenant | None:
    stmt = select(Tenant).where(Tenant.api_key == api_key)
    return (await db.execute(stmt)).scalars().first()


async def add_tenant(tenant: Tenant, db: AsyncSession) -> None:
    db.add(tenant)
    await db.flush()


async def update_tenant(
    tenant: Tenant,
    db: AsyncSession,
) -> Tenant:

    await db.flush()
    return tenant


async def list_dead_letters(
    tenant_id: int, db: AsyncSession
) -> Sequence[DeadLetterWebhook]:
    stmt = (
        select(DeadLetterWebhook)
        .where(DeadLetterWebhook.tenant_id == tenant_id)
        .order_by(DeadLetterWebhook.failed_at.desc())
    )
    return (await db.execute(stmt)).scalars().all()
