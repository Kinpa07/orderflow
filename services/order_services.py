from datetime import datetime
from db.storage import temp_db_orders, temp_db_tenants
from schemas.order import OrderCreate, OrderResponse, OrderResponseList
from models.order_status import OrderStatus
from models.order import Order
from fastapi import HTTPException

async def create_order(tenant_id: int, order: OrderCreate) -> OrderResponse:
    curr_tenant = next((tenant for tenant in temp_db_tenants if tenant.id == tenant_id), None)

    if not curr_tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    if curr_tenant.config.maximum_price is not None and order.price > curr_tenant.config.maximum_price:
        raise HTTPException(status_code=400, detail=f"Price exceeds maximum allowed price of {curr_tenant.config.maximum_price}")
    response = OrderResponse(
        id=len(temp_db_orders) + 1,
        tenant_id=tenant_id,
        price=order.price,
        status=OrderStatus.PENDING,
        created_at=datetime.now()
    )
    temp_db_orders.append(Order(**response.model_dump()))
    return response

async def list_order(tenant_id: int,
                     page: int = 1,
                    cursor_created_at: datetime | None = None,
                    cursor_id: int | None = None,
                    status: OrderStatus | None = None,
                    limit: int = 20,) -> OrderResponseList:


    if not cursor_id:
        offset = (page - 1) * limit
        response =[order for order in temp_db_orders if order.tenant_id == tenant_id][offset:offset + limit]
    else:
        response = [order for order in temp_db_orders if order.tenant_id == tenant_id and cursor_id < order.id][:limit]
    if status:
        response = [order for order in response if order.status == status]
    
    
    next_cursor = response[-1].id if (response and len(response) == limit) else None
    
    return OrderResponseList(orders=[OrderResponse(**order.__dict__) for order in response], next_cursor=next_cursor)