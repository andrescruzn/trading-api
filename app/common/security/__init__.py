# -*- coding: utf-8 -*-

# ======================================================================
# app/common/security/__init__.py
#
# Barrel exports del paquete security.
# - NO exporta utils de input_cleaner (eso va en common/utils).
# ======================================================================

from .jwt import (
    AuthException,
    JwtCodecError,
    create_access_token,
    decode_access_token,
    generate_jti,
    token_required_actual,
)

from .otp import generate_numeric_otp, hash_otp_sha1_hex
from .sanitization import sanitize_html
from .crypto_hash import sha1_hex

__all__ = [
    # JWT
    "AuthException",
    "JwtCodecError",
    "create_access_token",
    "decode_access_token",
    "generate_jti",
    "token_required_actual",

    # OTP
    "generate_numeric_otp",
    "hash_otp_sha1_hex",

    # Sanitization
    "sanitize_html",

    # Legacy hashing
    "sha1_hex",
]