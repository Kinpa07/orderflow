from dataclasses import dataclass

@dataclass
class Tenant:
    company_name: str
    contact_name: str
    email: str
    phone: str
    id: int | None = None
