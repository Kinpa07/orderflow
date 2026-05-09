from fastapi import APIRouter, Depends
from models.tenant import Tenant
from schemas.order import OrderResponse, OrderCreate, OrderResponseList
from models.order_status import OrderStatus
from datetime import datetime
from services.order_services import create_order, list_order
from dependencies.auth import verify_api_key

order_router = APIRouter()


@order_router.get("/", response_model=OrderResponseList)
async def list_orders(
    id: int,
    page: int = 1,
    cursor_created_at: datetime | None = None,
    cursor_id: int | None = None,
    status: OrderStatus | None = None,
    limit: int = 20,
    _: Tenant = Depends(verify_api_key)
):
    response = await list_order(id, page, cursor_created_at, cursor_id, status, limit)
    return response


@order_router.post("/", response_model=OrderResponse)
async def create_orders(id: int, order: OrderCreate, _: Tenant = Depends(verify_api_key)):
    response = await create_order(id, order)
    return response
