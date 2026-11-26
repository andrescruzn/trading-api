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
from .role_guard import (
    is_investor,
    is_partner,
    is_staff,
    is_super_admin,
    read_scope,
    staff_required,
    super_admin_required,
    write_scope,
)
from .auth_exceptions import AuthException

__all__ = [
    "JwtCodecError",
    "create_access_token",
    "decode_access_token",
    "generate_jti",
    "token_required_actual",
    "super_admin_required",
    "staff_required",
    "is_super_admin",
    "is_partner",
    "is_investor",
    "is_staff",
    "read_scope",
    "write_scope",
    "AuthException",
]