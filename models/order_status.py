import enum


class OrderStatus(enum.Enum):
    PENDING = "pending"
    SHIPPED = "shipped"
    PROCESSING = "processing"
    CANCELLED = "cancelled"
