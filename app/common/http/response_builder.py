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
