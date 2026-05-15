from models.tenant import Tenant
from fastapi import Depends, HTTPException, Header, Request
from dependencies.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.tenant_repository import get_tenant_by_api_key


async def verify_api_key(
    request: Request,
    api_key: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> Tenant:

    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")
    tenant = await get_tenant_by_api_key(api_key, db)

    if not tenant:
        raise HTTPException(status_code=401, detail="Invalid API key")

    request.state.tenant_id = tenant.id
    return tenant
