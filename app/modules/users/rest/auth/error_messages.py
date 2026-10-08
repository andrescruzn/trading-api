# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/rest/auth/error_messages.py
#
# Mensajes de error para el módulo de autenticación.
#
# NOTA:
# - Usa AUTH_ERROR_MESSAGES de common/errors como base.
# - Solo agrega mensajes específicos si es necesario.
# ======================================================================

from app.common.errors import AUTH_ERROR_MESSAGES

# Re-exportar para uso local (incluye todos los mensajes de auth)
DEFAULT_AUTH_ERROR_MESSAGES = AUTH_ERROR_MESSAGES

# POST /users/login/otp/verify: anti-enumeración.
# - Sin cuenta, sin código activo, vencido o incorrecto → mismo texto, para
#   que la respuesta no revele si el correo tiene cuenta.
_OTP_REJECTED_MESSAGE = "El código no es válido o ya venció. Revísalo o pide uno nuevo."

OTP_VERIFY_ERROR_MESSAGES: dict[str, str] = {
    **AUTH_ERROR_MESSAGES,
    "OTP_NOT_REQUESTED": _OTP_REJECTED_MESSAGE,
    "OTP_EXPIRED": _OTP_REJECTED_MESSAGE,
    "OTP_INVALID": _OTP_REJECTED_MESSAGE,
}