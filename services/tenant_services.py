from db.storage import temp_db_tenants
from schemas.tenant import TenantConfig, TenantCreate, TenantResponse
from models.tenant import Tenant
import uuid

async def create_tenant(tenant: TenantCreate) -> TenantResponse:
    result = Tenant(**tenant.model_dump(), id=len(temp_db_tenants) + 1, api_key=uuid.uuid4().hex)
    result.config = tenant.config 
    temp_db_tenants.append(result)
    return TenantResponse(**result.__dict__)