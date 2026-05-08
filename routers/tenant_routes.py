from fastapi import APIRouter
from schemas.tenant import TenantResponse, TenantCreate
from services.tenant_services import create_tenant
tenant_router = APIRouter()



@tenant_router.post("/", response_model=TenantResponse)
async def create_tenants(tenant: TenantCreate):
    response = await create_tenant(tenant)
    return response