from pydantic import BaseModel
from models.order_status import OrderStatus

class OrderCreate(BaseModel):
    price: float

class OrderResponse(BaseModel):
    id: int
    tenant_id: int
    price: float
    status: OrderStatus