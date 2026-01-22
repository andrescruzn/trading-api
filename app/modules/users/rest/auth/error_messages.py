# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/rest/auth/error_messages.py
#
# Mensajes de UI (solo REST).
# Los services retornan SOLO codes estables.
# ======================================================================

DEFAULT_AUTH_ERROR_MESSAGES = {
    "VALIDATION_ERROR": "Invalid request",
    "INVALID_REQUEST": "Invalid request",
    "USER_NOT_ALLOWED": "User not allowed",
    "LOGIN_LOCKED": "Too many failed attempts. Please try again later.",
    "INVALID_CREDENTIALS": "Invalid credentials",
    "OTP_NOT_REQUESTED": "OTP not requested",
    "OTP_EXPIRED": "OTP expired",
    "OTP_INVALID": "Invalid OTP",
    "OTP_EMAIL_SEND_FAILED": "Could not send OTP email",
}