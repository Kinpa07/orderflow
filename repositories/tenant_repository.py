from sqlalchemy import select

from models.tenant import Tenant
from sqlalchemy.ext.asyncio import AsyncSession


async def get_tenant(tenant_id: int, db: AsyncSession) -> Tenant | None:
    return await db.get(Tenant, tenant_id)

async def get_tenant_by_api_key(api_key: str, db: AsyncSession) -> Tenant | None:
    stmt = select(Tenant).where(Tenant.api_key == api_key)
    return (await db.execute(stmt)).scalars().first()

async def add_tenant(tenant: Tenant, db: AsyncSession) -> None:
    db.add(tenant)
    await db.flush()