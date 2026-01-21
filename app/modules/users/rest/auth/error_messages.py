# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/rest/auth/error_messages.py
#
# Mensajes por defecto del contexto AUTH.
# Esta ES capa de presentación (REST).
# ======================================================================

DEFAULT_AUTH_ERROR_MESSAGES = {
    "VALIDATION_ERROR": "Invalid request",
    "INVALID_REQUEST": "If the user exists, an OTP will be sent",
    "USER_NOT_ALLOWED": "User not allowed",
}