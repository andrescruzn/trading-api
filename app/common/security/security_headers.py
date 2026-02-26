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
# CSP por tipo de ruta
# ======================================================================

# Para páginas web (Jinja2): permite cargar recursos desde 'self' y CDNs usados
_CSP_WEB = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://unpkg.com; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com; "
    "img-src 'self' data:; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self';"
)

# Para endpoints API pura: política más restrictiva
_CSP_API = (
    "default-src 'none'; "
    "frame-ancestors 'none';"
)


def _is_web_route(path: str) -> bool:
    """
    Determina si la ruta sirve páginas HTML (usa CSP_WEB).
    Rutas /static/ y páginas web usan CSP más permisivo.
    """
    web_prefixes = (
        "/login", "/dashboard", "/profile",
        "/static/",
        "/market/", "/admin/",
    )
    return any(path.startswith(p) for p in web_prefixes) or path == "/"


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
        # CSP: diferente según tipo de ruta
        # ------------------------------------------------------------------
        csp = _CSP_WEB if _is_web_route(path) else _CSP_API
        response.headers["Content-Security-Policy"] = csp

        # ------------------------------------------------------------------
        # HSTS: solo en producción (requiere HTTPS)
        # ------------------------------------------------------------------
        if settings.APP_ENV not in ("development", "testing"):
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        return response
