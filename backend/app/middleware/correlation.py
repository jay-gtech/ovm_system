import logging
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core import context

logger = logging.getLogger(__name__)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Assign a UUID correlation ID to every inbound request.

    Behavior:
      - If the client supplies a valid UUID in the ``X-Request-ID`` header
        that value is reused (useful for end-to-end tracing across services).
      - Any non-UUID or missing value causes a fresh UUID to be generated,
        preventing header injection or ID spoofing.
      - The resolved ID is stored in the async-safe ``_request_id_ctx``
        ContextVar and echoed back on the response via ``X-Request-ID``.
      - The ContextVar is always reset in a ``finally`` block — even when
        ``call_next`` raises — so there is zero leakage between requests.

    Security note:
      Accepting a client-supplied UUID is safe because the value is parsed
      (not used raw) and is only used for tracing, never for authorization.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # ----------------------------------------------------------------
        # Resolve request ID: validate client header or mint a fresh one.
        # ----------------------------------------------------------------
        raw_header = request.headers.get("X-Request-ID")
        if raw_header:
            try:
                request_id = uuid.UUID(raw_header)
            except ValueError:
                # Malformed header — generate a fresh ID and log for audit.
                request_id = uuid.uuid4()
                logger.debug(
                    "Invalid X-Request-ID header received; generated new ID",
                    extra={"supplied_header": raw_header, "new_request_id": str(request_id)},
                )
        else:
            request_id = uuid.uuid4()

        # ----------------------------------------------------------------
        # Bind to context; always reset via token in finally.
        # ----------------------------------------------------------------
        token = context.set_request_id(request_id)

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = str(request_id)
            return response
        finally:
            # Guaranteed reset — protects against exception paths and
            # Starlette's background-task execution model.
            context.reset_request_id(token)
