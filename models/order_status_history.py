from datetime import datetime
from models.order_status import OrderStatus
from models.base import Base
from sqlalchemy import DateTime, ForeignKey, Integer, func, Enum
from sqlalchemy.orm import Mapped, mapped_column


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id"), nullable=False
    )
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
