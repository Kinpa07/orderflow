from pydantic import BaseModel
from models.order_status import OrderStatus
from datetime import datetime


class OrderCreate(BaseModel):
    price: float


class OrderResponse(BaseModel):
    id: int
    tenant_id: int
    price: float
    status: OrderStatus
    created_at: datetime


class OrderResponseList(BaseModel):
    orders: list[OrderResponse]
    next_cursor: int | None = None
