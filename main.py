import dataclasses
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from routers.tenant_routes import tenant_router
from routers.order_routes import order_router
from error import AppError
app = FastAPI()
@app.exception_handler(HTTPException)
async def app_error_handler(request, exc: HTTPException):
    error = AppError(message=exc.detail, code=exc.status_code, details=[])
    error ={"error": dataclasses.asdict(error)}
    return(
        JSONResponse(
            content=error,
            status_code=exc.status_code,
        )
    )
app.include_router(tenant_router, prefix="/tenants", tags=["tenants"])
app.include_router(order_router, prefix="/tenants/{id}/orders", tags=["orders"])

@app.get("/")
async def root():
    return {"message": "Hello World"}