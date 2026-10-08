# -*- coding: utf-8 -*-

# ======================================================================
# app/common/security/security_headers.py
#
# PROPÓSITO:
# - Middleware que agrega security headers a TODAS las respuestas.
#
# HEADERS:
# - X-Content-Type-Options   → Evita MIME sniffing (XSS vector)
# - X-Frame-Options          → Evita clickjacking
# - X-XSS-Protection         → Filtro XSS en browsers legacy
# - Referrer-Policy          → Controla info del referrer
# - Permissions-Policy       → Deshabilita APIs del browser no usadas
# - Content-Security-Policy  → Política de fuentes de contenido
# - Strict-Transport-Security → HTTPS forzado (solo producción)
# ======================================================================

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.common.config import settings


# ======================================================================
# CSP
# ======================================================================
# La API es headless: no sirve HTML propio, así que todas las respuestas
# llevan la política más restrictiva. La única excepción es la documentación
# interactiva de FastAPI (/docs, /redoc), que carga Swagger UI / ReDoc
# desde cdn.jsdelivr.net y usa un script inline para inicializarse.

_CSP_API = (
    "default-src 'none'; "
    "frame-ancestors 'none';"
)

_CSP_DOCS = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com; "
    "img-src 'self' data: https://fastapi.tiangolo.com https://cdn.redoc.ly; "
    "worker-src 'self' blob:; "
    "frame-ancestors 'none';"
)

_DOCS_PATHS = ("/docs", "/redoc")


def _is_docs_route(path: str) -> bool:
    """True para Swagger UI / ReDoc (incluye /docs/oauth2-redirect)."""
    return any(path == p or path.startswith(f"{p}/") for p in _DOCS_PATHS)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Agrega security headers a todas las respuestas HTTP.

    Registrar en app_factory.py:
        app.add_middleware(SecurityHeadersMiddleware)
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        path = request.url.path

        # ------------------------------------------------------------------
        # Headers universales (todas las respuestas)
        # ------------------------------------------------------------------
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=()"
        )

        # ------------------------------------------------------------------
        # CSP: restrictiva para toda la API; /docs y /redoc necesitan su CDN
        # ------------------------------------------------------------------
        csp = _CSP_DOCS if _is_docs_route(path) else _CSP_API
        response.headers["Content-Security-Policy"] = csp

        # ------------------------------------------------------------------
        # HSTS: solo en producción (requiere HTTPS)
        # ------------------------------------------------------------------
        if settings.APP_ENV not in ("development", "testing"):
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        return response
