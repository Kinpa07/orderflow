from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


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

    @model_validator(mode="after")
    def validate_email_contains_company_name(self) -> Self:
        if "@" not in self.email:
            raise ValueError("Invalid email address")
        if self.company_name.lower().replace(" ", "") not in self.email:
            raise ValueError("Email address must contain company name")
        return self


class TenantResponse(BaseModel):
    model_config = ConfigDict(extra="ignore", from_attributes=True)
    company_name: str
    contact_name: str
    email: str
    phone: str
    id: int
    api_key: str
