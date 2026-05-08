from db.storage import temp_db_tenants
from schemas.tenant import TenantCreate, TenantResponse
import uuid

async def create_tenant(tenant: TenantCreate) -> TenantResponse:
    response = TenantResponse(**tenant.model_dump(), id=len(temp_db_tenants) + 1, api_key=uuid.uuid4().hex)
    temp_db_tenants.append(response)
    return response