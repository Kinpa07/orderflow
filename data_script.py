from models.order_status import OrderStatus
from models.tenant import Tenant
from models.order import Order
from models.validate import validate_order
from models.validate import validate_tenant




orders = [
    Order(id=1, tenant_id=1, price=0, status=OrderStatus.PENDING),
    Order(id=2, tenant_id=1, price=200.0, status=OrderStatus.SHIPPED),
    Order(id=3, tenant_id=2, price=300.0, status=OrderStatus.CANCELLED),
    Order(id=4, tenant_id=2, price=400.0, status=OrderStatus.CANCELLED),
    Order(id=5, tenant_id=3, price=500.0, status=OrderStatus.PENDING),
]

tenants = [
    Tenant(id=1, company_name="Test", contact_name="Test", email="Test", phone="Test"),
    Tenant(id=2, company_name="Test2", contact_name="Test2", email="Test2", phone="Test2"),
    Tenant(id=3, company_name="Test3", contact_name="Test3", email="Test3", phone="Test3"),
    Tenant(id=4, company_name="Test4", contact_name="Test4", email="Test4", phone="Test4"),
    Tenant(id=5, company_name="Test5", contact_name="Test5", email="Test5", phone="Test5"),
]

errors_orders = []
errors_tenants = []


for order in orders:
    try:
        validate_order(order)
    except ValueError as e:
        errors_orders.append(f"Order {order.id} is invalid: {e}")
        continue
if not errors_orders:
    print("All orders are valid")
else:
    print("The following orders are invalid:")
    for error in errors_orders:
        print(error)


for tenant in tenants:
    try:
        validate_tenant(tenant)
    except ValueError as e:
        errors_tenants.append(f"Tenant {tenant.id} is invalid: {e}")
        continue
if not errors_tenants:
    print("All tenants are valid")

else:
    print("The following tenants are invalid:")
    for error in errors_tenants:
        print(error)

