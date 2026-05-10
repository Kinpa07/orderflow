import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from structlog import get_logger
from time import perf_counter

logger = get_logger()


class APIMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response_id = uuid.uuid4()
        start = perf_counter()
        logger.info(
            "Received request",
            request_id=str(response_id),
            method=request.method,
            endpoint=request.url.path,
        )
        response = await call_next(request)
        logger.info(
            "Sent response",
            request_id=str(response_id),
            duration=perf_counter() - start,
            status_code=response.status_code,
            tenant_id=request.state.tenant_id
            if hasattr(request.state, "tenant_id")
            else None,
        )
        return response
