from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies.db import get_db
from schemas.tenant import TenantCreate, TenantResponse
from services.tenant_services import create_tenant

tenant_router = APIRouter()


@tenant_router.post("/", response_model=TenantResponse)
async def create_tenants(
    tenant: TenantCreate, db: AsyncSession = Depends(get_db)
) -> TenantResponse:
    response = await create_tenant(tenant, db)
    return response
