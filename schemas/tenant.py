from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TenantConfig(BaseModel):
    maximum_price: float | None = Field(
        default=None, description="The maximum price for orders placed by the tenant."
    )


class TenantCreate(BaseModel):
    company_name: str
    contact_name: str
    email: str
    phone: str
    config: TenantConfig
    webhook_url: str | None = None


class TenantResponse(BaseModel):
    model_config = ConfigDict(extra="ignore", from_attributes=True)
    company_name: str
    contact_name: str
    email: str
    phone: str
    id: int
    api_key: str
    config: TenantConfig
    webhook_url: str | None = None


class TenantUpdate(BaseModel):
    company_name: str | None = None
    contact_name: str | None = None
    email: str | None = None
    phone: str | None = None
    config: TenantConfig | None = None
    webhook_url: str | None = None


class DeadLetterWebhookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tenant_id: int
    order_id: int
    webhook_url: str
    payload: str
    error_message: str
    failed_at: datetime


class DeadLetterWebhookListResponse(BaseModel):
    items: list[DeadLetterWebhookResponse]
    total: int
