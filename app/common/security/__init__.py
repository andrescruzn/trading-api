# -*- coding: utf-8 -*-

# ======================================================================
# app/common/security/__init__.py
# Barrel exports del paquete security
# ======================================================================

from .jwt import (
    JwtSettings,
    load_jwt_settings,
    create_access_token,
    decode_access_token,
    JwtCodecError,
    JwtIdentity,
    require_jwt_identity,
    token_required,
)
from .sanitization import sanitize_html
from .otp import (
    generate_numeric_otp,
    hash_otp_sha1_hex,
)

__all__ = [
    # JWT
    "JwtSettings",
    "load_jwt_settings",
    "create_access_token",
    "decode_access_token",
    "JwtCodecError",
    "JwtIdentity",
    "require_jwt_identity",
    "token_required",

    # Sanitization
    "sanitize_html",

    # OTP
    "generate_numeric_otp",
    "hash_otp_sha1_hex",
]