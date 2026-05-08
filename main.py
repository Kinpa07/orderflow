from fastapi import FastAPI
from routers.tenant_routes import tenant_router
from routers.order_routes import order_router
app = FastAPI()

app.include_router(tenant_router, prefix="/tenants", tags=["tenants"])
app.include_router(order_router, prefix="/tenants/{id}/orders", tags=["orders"])

@app.get("/")
async def root():
    return {"message": "Hello World"}