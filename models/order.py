from dataclasses import dataclass
from models.order_status import OrderStatus



@dataclass
class Order:
    tenant_id: int
    price: float
    status: OrderStatus
    id: int | None = None