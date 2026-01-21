# app/common/security/otp/otp_hasher.py
# -*- coding: utf-8 -*-

# ======================================================================
# app/common/security/otp/otp_hasher.py
#
# PROPÓSITO:
# - Hashear OTP antes de guardarlo en DB (mejor práctica).
#
# NOTA:
# - Como tu tabla guarda otp_code VARCHAR(255), guardaremos el hash.
# - Por ahora DEVOLVEMOS el OTP en la respuesta (temporal).
# ======================================================================

from __future__ import annotations

import hashlib


def hash_otp_sha1_hex(otp: str) -> str:
    """
    Hashea OTP con SHA1 hex (legacy/simple).

    Nota de seguridad:
    - Ideal sería HMAC/pepper o hash más fuerte, pero esto ya evita guardar OTP en claro.
    """
    return hashlib.sha1(otp.encode("utf-8")).hexdigest()