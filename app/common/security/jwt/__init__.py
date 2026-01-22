# -*- coding: utf-8 -*-

# ======================================================================
# app/common/security/jwt/__init__.py
#
# Barrel exports del submódulo JWT (alineado a tus archivos reales).
# ======================================================================

from .jwt_utils import (
    JwtCodecError,
    create_access_token,
    decode_access_token,
    generate_jti,
)

from .jwt_guard import token_required_actual
from .role_guard import admin_required
from .auth_exceptions import AuthException

__all__ = [
    "JwtCodecError",
    "create_access_token",
    "decode_access_token",
    "generate_jti",
    "token_required_actual",
    "admin_required",
    "AuthException",
]