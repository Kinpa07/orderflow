from dataclasses import dataclass, field
from datetime import datetime
from models.order_status import OrderStatus



@dataclass
class Order:
    tenant_id: int
    price: float
    status: OrderStatus
    id: int | None = None
    created_at: datetime | None = field(default_factory=datetime.now)