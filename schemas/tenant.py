from pydantic import BaseModel, Field

class TenantConfig(BaseModel):
    maximum_price: float | None = Field(default=None, description="The maximum price for orders placed by the tenant.")

class TenantCreate(BaseModel):
    company_name: str
    contact_name: str
    email: str
    phone: str
    config: TenantConfig

class TenantResponse(BaseModel):
    company_name: str
    contact_name: str
    email: str
    phone: str
    id: int
    api_key: str

