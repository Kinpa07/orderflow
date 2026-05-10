import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from structlog import get_logger
from time import perf_counter

logger = get_logger()


class APIMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        id = uuid.uuid4()
        start = perf_counter()
        logger.info("Received request", request_id = str(id),
                    method=request.method, 
                    endpoint=request.url.path,
                    )
        response = await call_next(request)
        logger.info("Sent response", request_id = str(id), duration=perf_counter() - start, status_code=response.status_code,
                    tenant_id=request.headers.get("api-key", "unknown"))
        return response