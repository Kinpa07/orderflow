from models.tenant import Tenant
from fastapi import Depends, HTTPException, Header, Request
from dependencies.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


async def verify_api_key(
    request: Request,
    api_key: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> Tenant:
    
    stmt = select(Tenant).where(Tenant.api_key == api_key)
    tenant = (await db.execute(stmt)).scalars().first()

    if not tenant:
        raise HTTPException(status_code=401, detail="Invalid API key")

    request.state.tenant_id = tenant.id
    return tenant
