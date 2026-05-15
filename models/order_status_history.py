from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base
from models.order_status import OrderStatus


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id"), nullable=False
    )
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
