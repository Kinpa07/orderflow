from schemas.tenant import TenantCreate, TenantResponse
from models.tenant import Tenant
import uuid
from sqlalchemy.ext.asyncio import AsyncSession


async def create_tenant(tenant: TenantCreate, db: AsyncSession) -> TenantResponse:
    result = Tenant(**tenant.model_dump(), api_key=uuid.uuid4().hex)
    db.add(result)
    await db.flush()
    return TenantResponse(**result.__dict__)
