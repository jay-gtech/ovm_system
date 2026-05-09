import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core import context
from app.services.metrics import metrics

logger = logging.getLogger(__name__)

class RequestTracingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request tracing, timing, and exception tracking.
    Assigns a UUID correlation ID to every inbound request.
    Records metrics and logs request lifecycle.
    """
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        raw_header = request.headers.get("X-Request-ID")
        if raw_header:
            try:
                request_id = uuid.UUID(raw_header)
            except ValueError:
                request_id = uuid.uuid4()
        else:
            request_id = uuid.uuid4()

        token = context.set_request_id(request_id)
        start_time = time.time()
        
        metrics.inc("api_requests_total")

        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000
            
            # Log request completion
            logger.info(
                f"HTTP {request.method} {request.url.path} completed in {process_time:.2f}ms",
                extra={
                    "endpoint": request.url.path,
                    "method": request.method,
                    "status": response.status_code,
                    "duration_ms": process_time,
                    "service": "api"
                }
            )
            
            # Update metrics
            metrics.observe("api_latency_sum", "api_requests_total", process_time)
            
            if response.status_code >= 400:
                metrics.inc("api_errors_total")

            response.headers["X-Request-ID"] = str(request_id)
            return response
            
        except Exception as exc:
            process_time = (time.time() - start_time) * 1000
            metrics.inc("api_errors_total")
            
            logger.error(
                f"HTTP {request.method} {request.url.path} failed: {str(exc)}",
                exc_info=exc,
                extra={
                    "endpoint": request.url.path,
                    "method": request.method,
                    "status": 500,
                    "duration_ms": process_time,
                    "error_type": type(exc).__name__,
                    "service": "api"
                }
            )
            raise
        finally:
            context.reset_request_id(token)
