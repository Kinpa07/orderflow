from db.storage import temp_db_orders
from schemas.order import OrderCreate, OrderResponse
from models.order_status import OrderStatus

async def create_order(tenant_id: int, order: OrderCreate) -> OrderResponse:
    response = OrderResponse(
        id=len(temp_db_orders) + 1,
        tenant_id=tenant_id,
        price=order.price,
        status=OrderStatus.PENDING
    )
    temp_db_orders.append(response)
    return response