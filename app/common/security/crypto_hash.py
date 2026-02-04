# -*- coding: utf-8 -*-

# ======================================================================
# app/common/security/crypto_hash.py
#
# [DEPRECADO] - Este módulo está deprecado.
#
# MIGRACIÓN:
# - Para passwords: usar app.common.security.password_hasher
# - Para OTP: usar app.common.security.otp.hash_otp
#
# Este archivo se mantiene solo para compatibilidad con código legacy.
# No usar en código nuevo.
# ======================================================================

from __future__ import annotations

import hashlib
import warnings


def sha1_hex(raw: str) -> str:
    """
    [DEPRECADO] Retorna SHA1 hex de un string UTF-8.

    Usar en su lugar:
    - password_hasher.hash_password() para passwords
    - otp.hash_otp() para OTPs
    """
    warnings.warn(
        "sha1_hex is deprecated. Use hash_password() or hash_otp() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()