import enum


class OrderStatus(enum.Enum):
    PENDING = "pending"
    SHIPPED = "shipped"
    CANCELLED = "cancelled"
