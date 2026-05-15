import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from models.tenant import Tenant
from repositories.tenant_repository import add_tenant
from schemas.tenant import TenantCreate, TenantResponse


async def create_tenant(tenant: TenantCreate, db: AsyncSession) -> TenantResponse:
    result = Tenant(**tenant.model_dump(), api_key=uuid.uuid4().hex)
    await add_tenant(result, db)
    return TenantResponse.model_validate(result)
