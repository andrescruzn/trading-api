# -*- coding: utf-8 -*-

# ======================================================================
# app/common/logging/middleware.py
#
# PROPÓSITO:
# - Middleware para logging de requests.
# - Establece request_id para trazabilidad.
#
# USO:
#     from app.common.logging.middleware import LoggingMiddleware
#     app.add_middleware(LoggingMiddleware)
# ======================================================================

from __future__ import annotations

import time
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .logger import (
    generate_request_id,
    set_request_id,
    clear_context,
    log_request,
    get_logger,
)


logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware que:
    1. Genera request_id único para cada request
    2. Lo agrega al header de respuesta (X-Request-ID)
    3. Mide duración del request
    4. Loguea request al finalizar
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        # ------------------------------------------------------------------
        # 1) Generar o usar request_id existente
        # ------------------------------------------------------------------
        request_id = request.headers.get("X-Request-ID") or generate_request_id()
        set_request_id(request_id)

        # ------------------------------------------------------------------
        # 2) Medir tiempo
        # ------------------------------------------------------------------
        start_time = time.perf_counter()

        try:
            # ------------------------------------------------------------------
            # 3) Procesar request
            # ------------------------------------------------------------------
            response: Response = await call_next(request)

            # ------------------------------------------------------------------
            # 4) Calcular duración
            # ------------------------------------------------------------------
            duration_ms = (time.perf_counter() - start_time) * 1000

            # ------------------------------------------------------------------
            # 5) Agregar header de request_id
            # ------------------------------------------------------------------
            response.headers["X-Request-ID"] = request_id

            # ------------------------------------------------------------------
            # 6) Log del request (excluir health checks)
            # ------------------------------------------------------------------
            if not request.url.path.startswith("/health"):
                log_request(
                    method=request.method,
                    path=request.url.path,
                    status_code=response.status_code,
                    duration_ms=duration_ms,
                )

            return response

        except Exception as e:
            # Log de error no capturado
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"Unhandled error: {e}",
                extra={
                    "http_method": request.method,
                    "http_path": request.url.path,
                    "duration_ms": round(duration_ms, 2),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
            raise

        finally:
            # ------------------------------------------------------------------
            # 7) Limpiar contexto
            # ------------------------------------------------------------------
            clear_context()
