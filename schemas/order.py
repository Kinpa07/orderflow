from datetime import datetime

from pydantic import BaseModel, ConfigDict

from models.order_status import OrderStatus


class OrderCreate(BaseModel):
    price: float


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tenant_id: int
    price: float
    status: OrderStatus
    priority: int
    created_at: datetime


class OrderResponseList(BaseModel):
    orders: list[OrderResponse]
    next_cursor: int | None = None
    next_cursor_created_at: datetime | None = None
