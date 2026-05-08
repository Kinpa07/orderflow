from fastapi import APIRouter
from schemas.tenant import TenantResponse, TenantCreate
tenant_router = APIRouter()



@tenant_router.post("/", response_model=TenantResponse)
async def create_tenant(tenant: TenantCreate):
    pass