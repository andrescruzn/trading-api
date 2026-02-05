# -*- coding: utf-8 -*-

# ======================================================================
# app/common/http/response_builder.py
#
# PROPÓSITO:
# - Funciones genéricas para construir respuestas HTTP.
# - Centraliza la lógica de presentación para TODO el proyecto.
# - Elimina duplicación entre módulos.
#
# UBICACIÓN:
# - Según CLAUDE.md, toda lógica reutilizable debe estar en app/common/
#
# USO:
#     from app.common.http import build_error_response, build_token_response
# ======================================================================

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, TypeVar

from fastapi.responses import JSONResponse

from app.common.contracts import ServiceResult
from app.common.http.http_responder import send
from app.common.utils import utc_to_bogota


T = TypeVar("T")


# ======================================================================
# Manejo de errores
# ======================================================================

def build_error_response(
    result: ServiceResult,
    error_messages: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Convierte ServiceResult con error en respuesta HTTP.

    Parámetros:
    - result: ServiceResult con success=False
    - error_messages: Diccionario {code: mensaje_ui} (opcional)
    """
    err = result.error

    if err is None:
        return send(msg="Error", status_code=500, data=[])

    messages = error_messages or {}
    msg = messages.get(err.code, err.code)

    return send(msg=msg, status_code=err.http_status, data=[])


def build_internal_error_response(
    msg: str = "Internal server error",
) -> Dict[str, Any]:
    """Respuesta de error interno (500)."""
    return send(msg=msg, status_code=500, data=[])


# ======================================================================
# Respuestas de éxito
# ======================================================================

def build_success_response(
    data: Optional[Any] = None,
    msg: str = "OK",
    status_code: int = 200,
) -> Dict[str, Any]:
    """Respuesta de éxito genérica."""
    return send(msg=msg, status_code=status_code, data=data or [])


def build_created_response(
    data: Optional[Any] = None,
    msg: str = "Created",
) -> Dict[str, Any]:
    """Respuesta de recurso creado (201)."""
    return send(msg=msg, status_code=201, data=data or [])


# ======================================================================
# Respuestas con transformación de fechas
# ======================================================================

def build_data_response(
    data: Dict[str, Any],
    datetime_fields: Optional[List[str]] = None,
    msg: str = "OK",
    status_code: int = 200,
) -> Dict[str, Any]:
    """
    Respuesta con transformación automática de fechas UTC -> Bogotá.

    Parámetros:
    - data: Diccionario con datos
    - datetime_fields: Campos datetime a convertir a Bogotá
    """
    result_data = data.copy()

    for field in (datetime_fields or []):
        if field in result_data and result_data[field] is not None:
            value = result_data[field]
            if isinstance(value, datetime):
                bogota_dt = utc_to_bogota(value)
                result_data[field] = bogota_dt.isoformat() if bogota_dt else None

    return send(msg=msg, status_code=status_code, data=result_data)


# ======================================================================
# Respuestas de listados
# ======================================================================

def build_list_response(
    items: List[Any],
    msg: str = "OK",
) -> Dict[str, Any]:
    """Respuesta de listado simple."""
    return send(msg=msg, status_code=200, data=items)


def build_paginated_response(
    items: List[Any],
    total: int,
    page: int,
    page_size: int,
    msg: str = "OK",
) -> Dict[str, Any]:
    """Respuesta de listado paginado."""
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    return send(
        msg=msg,
        status_code=200,
        data={
            "items": items,
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            },
        },
    )


# ======================================================================
# Respuestas de autenticación
# ======================================================================

def build_token_response(
    access_token: str,
    expires_at: datetime,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Respuesta de token JWT.

    Parámetros:
    - access_token: JWT emitido
    - expires_at: datetime UTC de expiración
    - extra: campos adicionales opcionales
    """
    data = {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_at": expires_at,
    }

    if extra:
        data.update(extra)

    return build_data_response(data=data, datetime_fields=["expires_at"])


def build_otp_required_response(
    email: str,
    otp_expires_at: datetime,
    otp_code: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Respuesta cuando se requiere OTP.

    Seguridad:
    - otp_code solo se incluye en desarrollo (APP_ENV=development)

    Parámetros:
    - email: email del usuario
    - otp_expires_at: datetime UTC de expiración del OTP
    - otp_code: código OTP (solo para desarrollo)
    """
    from app.common.config import settings

    data: Dict[str, Any] = {
        "otp_required": True,
        "email": email,
        "otp_expires_at": otp_expires_at,
    }

    if settings.APP_ENV == "development" and otp_code:
        data["otp_code"] = otp_code

    return build_data_response(data=data, datetime_fields=["otp_expires_at"])


# ======================================================================
# Respuestas de autenticación con cookies HTTP-only
# ======================================================================

def build_cookie_auth_response(
    access_token: str,
    expires_at: datetime,
    max_age_seconds: int,
) -> JSONResponse:
    """
    Respuesta de login exitoso con cookie HTTP-only.

    SEGURIDAD:
    - El token NO se devuelve en el body (evita almacenamiento en localStorage).
    - Se setea como cookie HttpOnly (JavaScript no puede leerla).
    - Secure=True en producción (solo HTTPS).
    - SameSite=Lax (protección CSRF básica).

    Parámetros:
    - access_token: JWT emitido
    - expires_at: datetime UTC de expiración del token
    - max_age_seconds: TTL de la cookie en segundos (sincronizado con JWT)

    Uso en React:
        fetch('/api/login', { credentials: 'include' })
        // No necesitas guardar nada, el browser maneja la cookie
    """
    from app.common.config import settings

    # --------------------------------------------------------------
    # 1) Construir body de respuesta (sin token)
    # --------------------------------------------------------------
    bogota_dt = utc_to_bogota(expires_at)
    body = {
        "msg": "OK",
        "errorCode": 200,
        "data": {
            "authenticated": True,
            "expires_at": bogota_dt.isoformat() if bogota_dt else None,
        },
    }

    # --------------------------------------------------------------
    # 2) Crear JSONResponse
    # --------------------------------------------------------------
    response = JSONResponse(content=body, status_code=200)

    # --------------------------------------------------------------
    # 3) Setear cookie HTTP-only con el token
    # --------------------------------------------------------------
    response.set_cookie(
        key=settings.AUTH_COOKIE_NAME,
        value=access_token,
        max_age=max_age_seconds,
        path=settings.AUTH_COOKIE_PATH,
        domain=settings.AUTH_COOKIE_DOMAIN,
        secure=settings.AUTH_COOKIE_SECURE,
        httponly=True,  # JavaScript NO puede leer esta cookie
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )

    return response


def build_logout_response() -> JSONResponse:
    """
    Respuesta de logout: limpia la cookie de autenticación.

    Setea la cookie con Max-Age=0 para que el browser la elimine.
    """
    from app.common.config import settings

    body = {
        "msg": "OK",
        "errorCode": 200,
        "data": {"authenticated": False},
    }

    response = JSONResponse(content=body, status_code=200)

    # --------------------------------------------------------------
    # Limpiar cookie (Max-Age=0 la elimina del browser)
    # --------------------------------------------------------------
    response.delete_cookie(
        key=settings.AUTH_COOKIE_NAME,
        path=settings.AUTH_COOKIE_PATH,
        domain=settings.AUTH_COOKIE_DOMAIN,
        secure=settings.AUTH_COOKIE_SECURE,
        httponly=True,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )

    return response


# ======================================================================
# Helper completo desde ServiceResult
# ======================================================================

def build_from_service_result(
    result: ServiceResult[T],
    error_messages: Optional[Dict[str, str]] = None,
    transform: Optional[Callable[[T], Dict[str, Any]]] = None,
    datetime_fields: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Construye respuesta completa desde ServiceResult.

    Maneja éxito y error automáticamente.

    Parámetros:
    - result: ServiceResult del service
    - error_messages: Diccionario de códigos -> mensajes UI
    - transform: Función para convertir data a dict
    - datetime_fields: Campos datetime a convertir a Bogotá
    """
    if not result.success:
        return build_error_response(result, error_messages)

    if result.data is None:
        return build_internal_error_response()

    if transform:
        data = transform(result.data)
    elif hasattr(result.data, "__dict__"):
        data = {k: v for k, v in result.data.__dict__.items() if not k.startswith("_")}
    elif isinstance(result.data, dict):
        data = result.data
    else:
        data = {"value": result.data}

    if datetime_fields:
        return build_data_response(data, datetime_fields=datetime_fields)

    return build_success_response(data=data)
