import dataclasses
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from routers.tenant_routes import tenant_router
from routers.order_routes import order_router
from error import AppError
import structlog
from middleware import APIMiddleware

structlog.configure(
    processors=[
        # Add timestamp field
        structlog.processors.TimeStamper(fmt="iso"),
        # Add level="info"/"error"
        structlog.stdlib.add_log_level,
        # Convert final event dict to JSON
        structlog.processors.JSONRenderer(),
    ],
)

app = FastAPI()

app.add_middleware(APIMiddleware)


@app.exception_handler(HTTPException)
async def app_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    error = AppError(message=exc.detail, code=exc.status_code, details=[])
    body = {"error": dataclasses.asdict(error)}
    return JSONResponse(
        content=body,
        status_code=exc.status_code,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    error = AppError(message="Validation error", code=422, details=list(exc.errors()))
    body = {"error": dataclasses.asdict(error)}
    return JSONResponse(
        content=body,
        status_code=422,
    )


@app.exception_handler(Exception)
async def server_error_handler(request: Request, _exc: Exception) -> JSONResponse:
    error = AppError(message="Internal server error", code=500, details=[])
    body = {"error": dataclasses.asdict(error)}
    return JSONResponse(
        content=body,
        status_code=500,
    )


app.include_router(tenant_router, prefix="/tenants", tags=["tenants"])
app.include_router(order_router, prefix="/tenants/{tenant_id}/orders", tags=["orders"])


@app.get("/health")
async def root() -> dict[str, str]:
    return {"status": "OK"}
