# -*- coding: utf-8 -*-

# ======================================================================
# app/common/errors/errors.py
#
# Handlers globales: todo error sale con el envelope {msg, errorCode, data}
# (la API es headless; el frontend tiene un único parser de respuestas).
#
# - AuthException / JwtCodecError -> 401/403 con mensaje de UI
# - RequestValidationError        -> 422 con la lista de campos inválidos
# - RateLimitExceeded             -> 429 + header Retry-After
# - HTTPException de Starlette    -> 404 (ruta inexistente), 405, etc.
# ======================================================================

from __future__ import annotations

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.common.errors.error_messages import AUTH_ERROR_MESSAGES, COMMON_ERROR_MESSAGES
from app.common.http import send
from app.common.security.jwt import AuthException, JwtCodecError
from app.common.security.rate_limiter import RateLimitExceeded


# Códigos estables por status para HTTPException sin código propio
_HTTP_STATUS_CODES: dict[int, str] = {
    401: "AUTH_REQUIRED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    429: "RATE_LIMIT_EXCEEDED",
}


def _format_wait(seconds: int) -> str:
    """45 → "45 segundos"; 61 → "2 minutos" (redondea hacia arriba)."""
    if seconds < 60:
        return "1 segundo" if seconds == 1 else f"{seconds} segundos"
    minutes = -(-seconds // 60)
    return "1 minuto" if minutes == 1 else f"{minutes} minutos"


def _validation_errors(exc: RequestValidationError) -> list[dict[str, str]]:
    """Normaliza los errores de Pydantic a [{field, message}] (sin el input crudo)."""
    errors: list[dict[str, str]] = []
    for err in exc.errors():
        loc = [str(part) for part in err.get("loc", ()) if part not in ("body", "query", "path")]
        errors.append({
            "field": ".".join(loc),
            "message": str(err.get("msg", "")),
        })
    return errors


def register_error_handlers(app) -> None:
    """
    Registra handlers globales.
    """

    # --------------------------------------------------------------
    # 1) AuthException (códigos estables del guard JWT / roles)
    # --------------------------------------------------------------
    @app.exception_handler(AuthException)
    async def auth_exception_handler(request: Request, exc: AuthException):
        return send(
            msg=AUTH_ERROR_MESSAGES.get(exc.code, exc.code),
            status_code=exc.http_status,
            data=[],
        )

    # --------------------------------------------------------------
    # 2) JwtCodecError (fallback defensivo)
    # --------------------------------------------------------------
    @app.exception_handler(JwtCodecError)
    async def jwt_codec_exception_handler(request: Request, exc: JwtCodecError):
        return send(
            msg=AUTH_ERROR_MESSAGES["AUTH_INVALID_TOKEN"],
            status_code=401,
            data=[],
        )

    # --------------------------------------------------------------
    # 3) Validación de Pydantic (body / query / path)
    # --------------------------------------------------------------
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return send(
            msg=COMMON_ERROR_MESSAGES["VALIDATION_ERROR"],
            status_code=422,
            data=_validation_errors(exc),
        )

    # --------------------------------------------------------------
    # 4) Rate limit (auth)
    # --------------------------------------------------------------
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded):
        response = send(
            msg=COMMON_ERROR_MESSAGES["RATE_LIMIT_EXCEEDED_RETRY"].format(
                wait=_format_wait(exc.retry_after_seconds)
            ),
            status_code=429,
            data={"retry_after_seconds": exc.retry_after_seconds},
        )
        response.headers["Retry-After"] = str(exc.retry_after_seconds)
        return response

    # --------------------------------------------------------------
    # 5) HTTPException genérica (404 de ruta inexistente, 405, …)
    # --------------------------------------------------------------
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        code = _HTTP_STATUS_CODES.get(exc.status_code)
        if code:
            msg = COMMON_ERROR_MESSAGES.get(code, code)
        elif isinstance(exc.detail, str) and exc.detail:
            msg = exc.detail
        else:
            msg = COMMON_ERROR_MESSAGES["INTERNAL_ERROR"]
        response = send(msg=msg, status_code=exc.status_code, data=[])
        if exc.headers:
            response.headers.update(exc.headers)
        return response
