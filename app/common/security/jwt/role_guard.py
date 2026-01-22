# -*- coding: utf-8 -*-

# ======================================================================
# app/common/security/jwt/role_guard.py
#
# PROPÓSITO:
# - Guards de autorización por rol usando la identidad validada por DB.
#
# REGLA:
# - admin accede a todo.
# ======================================================================

from __future__ import annotations

from typing import Any, Dict

from fastapi import Depends

from app.common.config import settings
from app.common.security.jwt.auth_exceptions import AuthException
from app.common.security.jwt.jwt_guard import token_required_actual


def admin_required(identity: Dict[str, Any] = Depends(token_required_actual)) -> Dict[str, Any]:
    """
    Permite acceso SOLO a ADMIN.

    - Usa role_id obtenido desde DB por token_required_actual.
    """
    role_id = identity.get("role_id")

    if role_id is None:
        raise AuthException(code="AUTH_INVALID_IDENTITY", http_status=401)

    if int(role_id) != int(settings.AUTH_ADMIN_ROLE_ID):
        raise AuthException(code="AUTH_FORBIDDEN_ROLE", http_status=403, meta={"required": "admin"})

    return identity