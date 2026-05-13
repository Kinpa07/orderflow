from fastapi import APIRouter, Depends
from schemas.tenant import TenantResponse, TenantCreate
from services.tenant_services import create_tenant
from dependencies.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession

tenant_router = APIRouter()


@tenant_router.post("/", response_model=TenantResponse)
async def create_tenants(tenant: TenantCreate, db: AsyncSession = Depends(get_db)) -> TenantResponse:
    response = await create_tenant(tenant, db)
    return response
