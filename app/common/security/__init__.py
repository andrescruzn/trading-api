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

from .otp import generate_numeric_otp, hash_otp, verify_otp_hash, hash_otp_sha1_hex
from .sanitization import sanitize_html
from .crypto_hash import sha1_hex
from .password_hasher import hash_password, verify_password
from .rate_limiter import (
    RateLimiter,
    auth_rate_limiter,
    default_rate_limiter,
    rate_limit_dependency,
    check_auth_rate_limit,
)

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
    "hash_otp",
    "verify_otp_hash",
    "hash_otp_sha1_hex",  # Deprecado

    # Sanitization
    "sanitize_html",

    # Password hashing (bcrypt + legacy migration)
    "hash_password",
    "verify_password",

    # Rate limiting
    "RateLimiter",
    "auth_rate_limiter",
    "default_rate_limiter",
    "rate_limit_dependency",
    "check_auth_rate_limit",

    # Legacy hashing (deprecated, use verify_password instead)
    "sha1_hex",
]