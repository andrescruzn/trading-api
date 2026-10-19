# -*- coding: utf-8 -*-

# ======================================================================
# app/common/security/origin_guard.py
#
# PROPÓSITO:
# - Defensa CSRF adicional a SameSite: toda petición que cambia estado
#   (POST/PUT/PATCH/DELETE) y trae `Origin` debe venir de un origen de
#   CORS_ORIGINS. Si no, 403 con el envelope.
#
# DECISIÓN:
# - Los navegadores siempre envían `Origin` en peticiones POST/PUT/PATCH/
#   DELETE hechas con fetch, así que una página ajena no puede omitirlo.
# - Sin `Origin` (curl, Telegram, servidores) se deja pasar: esas
#   peticiones no llevan la cookie del navegador de la víctima.
# - Con SameSite=None (front en otro dominio) esta es la defensa principal.
# ======================================================================

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.common.config import settings

_UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


class OriginGuardMiddleware(BaseHTTPMiddleware):
    """Rechaza escrituras cuyo `Origin` no esté en CORS_ORIGINS."""

    def __init__(self, app, allowed_origins: list[str] | None = None):
        super().__init__(app)
        origins = allowed_origins if allowed_origins is not None else settings.CORS_ORIGINS
        self._allowed = frozenset(origin.rstrip("/") for origin in origins)

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method in _UNSAFE_METHODS:
            origin = request.headers.get("origin")
            if origin is not None and origin.rstrip("/") not in self._allowed:
                return JSONResponse(
                    status_code=403,
                    content={
                        "msg": "No se permite esta acción desde ese sitio.",
                        "errorCode": 403,
                        "data": [],
                    },
                )
        return await call_next(request)
