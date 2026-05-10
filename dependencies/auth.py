from db.storage import temp_db_tenants
from models.tenant import Tenant
from fastapi import HTTPException, Header, Request

async def verify_api_key(request: Request ,api_key: str | None = Header(default=None)) -> Tenant:
    tenant = next((tenant for tenant in temp_db_tenants if tenant.api_key == api_key), None)
    if not tenant:
        raise HTTPException(status_code=401, detail="Invalid API key")

    request.state.tenant_id = tenant.id
    return tenant