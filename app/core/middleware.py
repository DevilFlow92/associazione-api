"""
app.core.middleware
~~~~~~~~~~~~~~~~~~~
Request middleware: genera un UUID per ogni request, lo lega al contesto
async via associazione_toolkit.logging.bind_request_id, e logga il
completamento con metodo, path, status code e durata.
"""

from __future__ import annotations

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import bind_request_id, get_logger

logger = get_logger(__name__)


class RequestMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        start_time = time.perf_counter()

        # Lega il request_id al contesto async corrente —
        # tutti i log emessi durante questa request lo includeranno
        # automaticamente senza doverlo passare esplicitamente.
        bind_request_id(request_id)
        request.state.request_id = request_id

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        logger.info(
            "request completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms}ms"

        return response
