# -*- coding: utf-8 -*-

# ======================================================================
# app/common/audit/audit_middleware.py
#
# PROPÓSITO:
# - Capturar todos los requests HTTP y registrarlos en auditoría.
# - Non-blocking: el insert se lanza en un hilo daemon.
#
# FLUJO:
#   1. Skip rutas excluidas (/health, /static/, /favicon)
#   2. Leer request body (ya buffereado por BaseHTTPMiddleware)
#   3. Ejecutar request → capturar response body
#   4. Extraer user_id del JWT (silencioso si falla)
#   5. Resolver event_type según method+path+payload
#   6. Sanitizar payloads (redactar campos sensibles)
#   7. Lanzar hilo daemon NON-BLOCKING → insert en BD
#   8. Retornar response reconstruida al cliente
# ======================================================================

from __future__ import annotations

import logging
import threading
import time
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.common.audit.audit_repository import AuditRepository
from app.common.audit.audit_sanitizer import sanitize_request, sanitize_response
from app.common.config import settings
from app.common.security.jwt.jwt_utils import decode_access_token

logger = logging.getLogger(__name__)

# ======================================================================
# Configuración
# ======================================================================

# Rutas excluidas de auditoría
_SKIP_PREFIXES = ("/health", "/static/", "/favicon")

# Límite de body a auditar (10 KB) — evita memoria excesiva con uploads
_MAX_BODY_BYTES = 10 * 1024

# ======================================================================
# Mapeo de event_type
# ======================================================================

def _resolve_event_type(method: str, path: str, req_payload: dict | None) -> str:
    """
    Resuelve el event_type semántico según el endpoint llamado.

    POST /users/login distingue PASSWORD vs OTP por presencia de
    "password" en el payload (antes de redactar — se recibe el dict
    ya sanitizado, así que chequeamos la clave, no el valor).
    """
    # Normalizar path (quitar trailing slash)
    norm = path.rstrip("/")

    if method == "POST" and norm == "/users/login":
        # La clave "password" existe aunque su valor sea ***REDACTED***
        if req_payload and "password" in req_payload:
            return "LOGIN_PASSWORD"
        return "LOGIN_OTP_REQUEST"

    _EVENT_MAP: dict[tuple[str, str], str] = {
        ("POST",  "/users/login/otp/verify"): "VERIFY_OTP",
        ("POST",  "/users/logout"):            "LOGOUT",
        ("GET",   "/users/me"):                "GET_PROFILE",
        ("PATCH", "/users/me/password"):       "CHANGE_PASSWORD",
        ("POST",  "/users/token/rotate"):      "ROTATE_TOKEN",
    }

    return _EVENT_MAP.get((method, norm), "HTTP_REQUEST")


# ======================================================================
# Extracción de user_id desde JWT en cookie
# ======================================================================

def _extract_user_id(request: Request) -> int | None:
    """
    Extrae user_id del token JWT almacenado en cookie HTTP-only.

    Retorna None si no hay cookie, el token es inválido, o expiró.
    Nunca lanza excepción.
    """
    try:
        token = request.cookies.get(settings.AUTH_COOKIE_NAME)
        if not token:
            return None

        payload = decode_access_token(
            token=token,
            secret_key=settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        sub = payload.get("sub", {})
        if isinstance(sub, dict):
            return sub.get("user_id")
        return None
    except Exception:
        return None


# ======================================================================
# Middleware
# ======================================================================

class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware de auditoría HTTP dinámica por año.

    Registra cada request en http_audit_{year} de forma non-blocking.
    """

    def __init__(self, app, repository: AuditRepository) -> None:
        super().__init__(app)
        self._repo = repository

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # ------------------------------------------------------------------
        # 1. Skip rutas excluidas
        # ------------------------------------------------------------------
        path = request.url.path
        if any(path.startswith(prefix) for prefix in _SKIP_PREFIXES):
            return await call_next(request)

        # ------------------------------------------------------------------
        # 2. Leer request body (BaseHTTPMiddleware ya lo bufferiza)
        # ------------------------------------------------------------------
        body_bytes: bytes = await request.body()

        # No auditar body de requests muy grandes (ej: uploads)
        req_body_to_audit = body_bytes if len(body_bytes) <= _MAX_BODY_BYTES else b""

        # ------------------------------------------------------------------
        # 3. Extraer metadatos del request
        # ------------------------------------------------------------------
        method = request.method
        ip = _get_client_ip(request)
        user_agent = request.headers.get("user-agent")
        referer = request.headers.get("referer")

        # ------------------------------------------------------------------
        # 4. Ejecutar el request y medir duración
        # ------------------------------------------------------------------
        start_time = time.perf_counter()
        response: Response = await call_next(request)
        duration_ms = int((time.perf_counter() - start_time) * 1000)

        # ------------------------------------------------------------------
        # 5. Capturar response body y reconstruir la respuesta
        #    (necesario porque body_iterator solo se puede leer una vez)
        # ------------------------------------------------------------------
        chunks = [chunk async for chunk in response.body_iterator]
        response_body = b"".join(chunks)

        rebuilt = Response(
            content=response_body,
            status_code=response.status_code,
            media_type=response.media_type,
        )
        # Preservar headers originales (set-cookie, etc.)
        rebuilt.raw_headers = list(response.raw_headers)
        rebuilt.headers["content-length"] = str(len(response_body))

        # ------------------------------------------------------------------
        # 6. Extraer user_id (silencioso — falla → None)
        # ------------------------------------------------------------------
        user_id = _extract_user_id(request)

        # ------------------------------------------------------------------
        # 7. Sanitizar payloads
        # ------------------------------------------------------------------
        req_payload = sanitize_request(req_body_to_audit)
        resp_payload = sanitize_response(response_body)

        # ------------------------------------------------------------------
        # 8. Resolver event_type
        # ------------------------------------------------------------------
        event_type = _resolve_event_type(method, path, req_payload)

        # ------------------------------------------------------------------
        # 9. Insertar en BD de forma non-blocking (hilo daemon)
        # ------------------------------------------------------------------
        threading.Thread(
            target=self._repo.insert,
            kwargs=dict(
                user_id=user_id,
                event_type=event_type,
                method=method,
                path=path,
                status_code=response.status_code,
                ip=ip,
                user_agent=user_agent,
                referer=referer,
                request_payload=req_payload,
                response_payload=resp_payload,
                duration_ms=duration_ms,
            ),
            daemon=True,
        ).start()

        return rebuilt


# ======================================================================
# Helper: IP real con soporte X-Forwarded-For
# ======================================================================

def _get_client_ip(request: Request) -> str | None:
    """
    Extrae la IP del cliente.

    Prioriza X-Forwarded-For (proxy/load balancer) sobre la IP directa.
    """
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        # Tomar la primera IP de la lista (la del cliente original)
        return forwarded_for.split(",")[0].strip()

    if request.client:
        return request.client.host

    return None
