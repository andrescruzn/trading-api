# -*- coding: utf-8 -*-

# ======================================================================
# app/common/errors/errors.py
#
# Handler global: AuthException -> envelope send()
# ======================================================================

from __future__ import annotations

from app.common.http import send
from app.common.security.jwt import AuthException, JwtCodecError


def register_error_handlers(app) -> None:
    """
    Registra handlers globales.
    """

    # --------------------------------------------------------------
    # 1) AuthException (códigos estables)
    # --------------------------------------------------------------
    @app.exception_handler(AuthException)
    async def auth_exception_handler(request, exc: AuthException):
        # ✅ send() debe retornar una Response (JSONResponse) lista
        return send(
            msg=exc.code,
            status_code=exc.http_status,
            data=[],
        )

    # --------------------------------------------------------------
    # 2) JwtCodecError (fallback defensivo)
    # --------------------------------------------------------------
    @app.exception_handler(JwtCodecError)
    async def jwt_codec_exception_handler(request, exc: JwtCodecError):
        return send(
            msg="AUTH_INVALID_TOKEN",
            status_code=401,
            data=[],
        )