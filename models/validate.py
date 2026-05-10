from models.tenant import Tenant
from models.order import Order


def validate_not_null(value: int | str | None, field_name : str) -> None:
    if value is None:
        raise ValueError(f"{field_name} cannot be null")

def validate_not_below_zero(value: int | float, field_name : str) -> None:
    if value <= 0:
        raise ValueError(f"{field_name} cannot be zero or below")



def validate_order(order: Order) -> None:
    validate_not_null(order.tenant_id, "tenant_id")
    validate_not_below_zero(order.price, "price")
    

def validate_tenant(tenant: Tenant) -> None:
    validate_not_null(tenant.company_name, "company_name")
    validate_not_null(tenant.contact_name, "contact_name")
    validate_not_null(tenant.email, "email")
    validate_not_null(tenant.phone, "phone")