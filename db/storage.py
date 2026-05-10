from models.tenant import Tenant
from models.order import Order

temp_db_tenants: list[Tenant] = []
temp_db_orders: list[Order] = []

print("Initialized in-memory storage for tenants and orders")
