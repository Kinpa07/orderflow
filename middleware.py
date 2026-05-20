import uuid
from time import perf_counter

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from structlog import get_logger

from metrics import (
    http_request_duration_seconds,
    http_requests_in_progress,
    http_requests_total,
)

logger = get_logger()


class APIMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        method = request.method
        endpoint = request.url.path
        request_id = str(uuid.uuid4())

        http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()
        start = perf_counter()

        logger.info(
            "Received request",
            request_id=request_id,
            method=method,
            endpoint=endpoint,
        )

        try:
            response = await call_next(request)
        finally:
            http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()

        duration = perf_counter() - start

        http_requests_total.labels(
            method=method, endpoint=endpoint, status=str(response.status_code)
        ).inc()
        http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(
            duration
        )

        logger.info(
            "Sent response",
            request_id=request_id,
            duration=duration,
            status_code=response.status_code,
            tenant_id=request.state.tenant_id
            if hasattr(request.state, "tenant_id")
            else None,
        )

        return response
