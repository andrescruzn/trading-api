# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/services/__init__.py
#
# Barrel exports del módulo users.services
#
# OBJETIVO:
# - Exponer públicamente (API interna) los servicios principales del módulo users
# - Evitar imports largos desde subcarpetas (screaming architecture)
#
# NOTA:
# - Re-exportamos desde users.services.auth (subcontexto auth)
# ======================================================================

from .auth import (
    LoginOtpPayload,
    LoginOtpService,
    LoginPasswordPayload,
    LoginPasswordService,
    VerifyOtpPayload,
    VerifyOtpService,
    LogoutService,
    RotateTokenPayload,
    RotateTokenService,
)

__all__ = [
    # Login OTP
    "LoginOtpService",
    "LoginOtpPayload",
    # Login Password
    "LoginPasswordService",
    "LoginPasswordPayload",
    # Verify OTP
    "VerifyOtpService",
    "VerifyOtpPayload",
    # Logout
    "LogoutService",
    # Rotate token
    "RotateTokenService",
    "RotateTokenPayload",
]