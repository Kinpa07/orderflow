import uuid
from time import perf_counter

import structlog.contextvars
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from structlog import get_logger

from config import MAX_BODY_SIZE
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
        if request.url.path.startswith("/metrics"):
            return await call_next(request)

        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_BODY_SIZE:
            return JSONResponse(
                status_code=413,
                content={
                    "error": {
                        "message": (
                            f"Request body exceeds the {MAX_BODY_SIZE} byte limit"
                        ),
                        "code": 413,
                        "details": [],
                    }
                },
            )

        method = request.method
        endpoint = request.url.path
        request_id = str(uuid.uuid4())

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        request.state.request_id = request_id

        http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()
        start = perf_counter()

        logger.info(
            "Received request",
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
            duration=duration,
            status_code=response.status_code,
            tenant_id=request.state.tenant_id
            if hasattr(request.state, "tenant_id")
            else None,
        )

        return response
