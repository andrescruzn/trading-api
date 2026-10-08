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
    "VALIDATION_ERROR": "Revisa los datos enviados: hay campos inválidos o incompletos.",
    "INVALID_REQUEST": "La solicitud no es válida.",
    "MISSING_REQUIRED_FIELD": "Falta un campo obligatorio.",
    "INVALID_FORMAT": "El formato de un campo no es válido.",

    # Autenticación
    "AUTH_REQUIRED": "Inicia sesión para continuar.",
    "AUTH_INVALID_TOKEN": "Tu sesión no es válida o expiró. Inicia sesión de nuevo.",
    "AUTH_MISSING_TOKEN": "Inicia sesión para continuar.",
    "AUTH_SESSION_REVOKED": "Tu sesión se cerró porque iniciaste sesión en otro lugar.",
    "AUTH_INVALID_TOKEN_TYPE": "Tu sesión no es válida. Inicia sesión de nuevo.",
    "AUTH_INVALID_SUBJECT": "Tu sesión no es válida. Inicia sesión de nuevo.",
    "AUTH_INVALID_IDENTITY": "Tu sesión no es válida. Inicia sesión de nuevo.",
    "AUTH_MISSING_JTI": "Tu sesión no es válida. Inicia sesión de nuevo.",
    "AUTH_USER_NOT_FOUND": "Tu usuario ya no existe o está inactivo.",
    "AUTH_ROLE_NOT_FOUND": "Tu usuario no tiene un rol válido. Contacta al administrador.",
    "AUTH_ROLE_INACTIVE": "Tu rol está desactivado. Contacta al administrador.",
    "AUTH_FORBIDDEN_ROLE": "No tienes permiso para hacer esta acción.",

    # Autorización
    "FORBIDDEN": "No tienes permiso para hacer esta acción.",
    "ACCESS_DENIED": "No tienes acceso a este recurso.",

    # Rate limiting
    "RATE_LIMIT_EXCEEDED": "Demasiados intentos. Espera un momento y vuelve a intentarlo.",

    # Recursos
    "NOT_FOUND": "No encontramos lo que buscas.",
    "METHOD_NOT_ALLOWED": "Este endpoint no acepta ese método HTTP.",
    "ALREADY_EXISTS": "Ya existe un registro con esos datos.",
    "CONFLICT": "El registro cambió o entra en conflicto con otro.",

    # Estado
    "INVALID_STATE": "No se puede hacer esta acción en el estado actual.",
    "OPERATION_NOT_ALLOWED": "Esta operación no está permitida.",

    # Servidor
    "INTERNAL_ERROR": "Algo falló en el servidor. Inténtalo de nuevo en unos minutos.",
    "SERVICE_UNAVAILABLE": "El servicio no está disponible en este momento.",
    "EXTERNAL_SERVICE_ERROR": "Un servicio externo no respondió. Inténtalo de nuevo más tarde.",
}


# ======================================================================
# Errores de autenticación (específicos del módulo users)
# ======================================================================

AUTH_ERROR_MESSAGES: Dict[str, str] = {
    **COMMON_ERROR_MESSAGES,

    # Login
    "USER_NOT_ALLOWED": "Tu cuenta no está activa. Contacta al administrador.",
    "LOGIN_LOCKED": "Bloqueamos tu cuenta temporalmente por varios intentos fallidos. Inténtalo más tarde.",

    # OTP
    "OTP_NOT_REQUESTED": "No hay un código activo. Pide uno nuevo.",
    "OTP_EXPIRED": "El código venció. Pide uno nuevo.",
    "OTP_INVALID": "El código no es correcto. Revísalo e inténtalo de nuevo.",
    "OTP_EMAIL_SEND_FAILED": "No pudimos enviarte el correo con el código. Inténtalo más tarde.",

    # Sesión
    "SESSION_EXPIRED": "Tu sesión expiró. Inicia sesión de nuevo.",
    "SESSION_INVALID": "Tu sesión no es válida. Inicia sesión de nuevo.",

    # Usuario
    "USER_NOT_FOUND": "No encontramos tu usuario.",
    "ROLE_NOT_FOUND": "Tu usuario no tiene un rol válido. Contacta al administrador.",
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
