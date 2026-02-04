# -*- coding: utf-8 -*-

# ======================================================================
# app/common/errors/error_messages.py
#
# PROPÓSITO:
# - Mensajes de error comunes reutilizables por todos los módulos.
# - Centraliza mensajes genéricos (validación, auth, etc.).
#
# USO:
#     from app.common.errors import COMMON_ERROR_MESSAGES
#
#     # En tu módulo, combina con mensajes específicos:
#     MODULE_ERROR_MESSAGES = {
#         **COMMON_ERROR_MESSAGES,
#         "ORDER_NOT_FOUND": "Order not found",
#     }
#
# PRINCIPIO:
# - Services retornan SOLO códigos estables (ej: "VALIDATION_ERROR").
# - REST traduce códigos a mensajes de UI usando estos diccionarios.
# ======================================================================

from typing import Dict


# ======================================================================
# Errores comunes (reutilizables por todos los módulos)
# ======================================================================

COMMON_ERROR_MESSAGES: Dict[str, str] = {
    # Validación
    "VALIDATION_ERROR": "Invalid request data",
    "INVALID_REQUEST": "Invalid request",
    "MISSING_REQUIRED_FIELD": "Missing required field",
    "INVALID_FORMAT": "Invalid format",

    # Autenticación
    "AUTH_REQUIRED": "Authentication required",
    "AUTH_INVALID_TOKEN": "Invalid or expired token",
    "AUTH_MISSING_TOKEN": "Missing authentication token",
    "AUTH_SESSION_REVOKED": "Session has been revoked",

    # Autorización
    "FORBIDDEN": "You don't have permission to perform this action",
    "ACCESS_DENIED": "Access denied",

    # Rate limiting
    "RATE_LIMIT_EXCEEDED": "Too many requests. Please try again later.",

    # Recursos
    "NOT_FOUND": "Resource not found",
    "ALREADY_EXISTS": "Resource already exists",
    "CONFLICT": "Resource conflict",

    # Estado
    "INVALID_STATE": "Invalid state for this operation",
    "OPERATION_NOT_ALLOWED": "Operation not allowed",

    # Servidor
    "INTERNAL_ERROR": "Internal server error",
    "SERVICE_UNAVAILABLE": "Service temporarily unavailable",
    "EXTERNAL_SERVICE_ERROR": "External service error",
}


# ======================================================================
# Errores de autenticación (específicos del módulo users)
# ======================================================================

AUTH_ERROR_MESSAGES: Dict[str, str] = {
    **COMMON_ERROR_MESSAGES,

    # Login
    "INVALID_CREDENTIALS": "Invalid credentials",
    "USER_NOT_ALLOWED": "User account is not active",
    "LOGIN_LOCKED": "Too many failed attempts. Please try again later.",

    # OTP
    "OTP_NOT_REQUESTED": "OTP was not requested",
    "OTP_EXPIRED": "OTP has expired",
    "OTP_INVALID": "Invalid OTP code",
    "OTP_EMAIL_SEND_FAILED": "Could not send OTP email",

    # Sesión
    "SESSION_EXPIRED": "Session has expired",
    "SESSION_INVALID": "Invalid session",
}


# ======================================================================
# Helper para combinar mensajes
# ======================================================================

def merge_error_messages(*dicts: Dict[str, str]) -> Dict[str, str]:
    """
    Combina múltiples diccionarios de mensajes de error.

    Uso:
        TRADING_ERROR_MESSAGES = merge_error_messages(
            COMMON_ERROR_MESSAGES,
            {"ORDER_NOT_FOUND": "Order not found"},
        )
    """
    result: Dict[str, str] = {}
    for d in dicts:
        result.update(d)
    return result
