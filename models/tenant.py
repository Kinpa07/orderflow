from dataclasses import dataclass
from schemas.tenant import TenantConfig

@dataclass
class Tenant:
    company_name: str
    contact_name: str
    email: str
    phone: str
    id: int | None = None
    config: TenantConfig | None = None
    api_key: str | None = None

