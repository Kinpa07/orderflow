from fastapi import APIRouter
from schemas.order import OrderResponse, OrderCreate
from models.order_status import OrderStatus
from datetime import datetime
from services.order_services import create_order

order_router = APIRouter()


@order_router.get("/", response_model=list[OrderResponse])
async def list_orders(
    id: int,
    cursor_created_at: datetime | None = None,
    cursor_id: int | None = None,
    status: OrderStatus | None = None,
    limit: int = 20,
):
    pass


@order_router.post("/", response_model=OrderResponse)
async def create_orders(id: int, order: OrderCreate):
    response = await create_order(id, order)
    return response
