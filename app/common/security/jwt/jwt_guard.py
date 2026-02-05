# -*- coding: utf-8 -*-

# ======================================================================
# app/common/security/jwt/jwt_guard.py
#
# PROPÓSITO:
# - Dependency que protege endpoints validando:
#   1) JWT firma/exp
#   2) type=access
#   3) sub={"user_id": ...}
#   4) jti presente
#   5) DB: user.token_current_jti == jti
#   6) Role del usuario existe y está activo (roles.is_active=1)
#
# FUENTES DEL TOKEN (en orden de prioridad):
# - Cookie HTTP-only (para React SPA)
# - Bearer header (para APIs, mobile, testing)
# ======================================================================

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.common.config import settings
from app.extensions.db import get_db
from app.modules.users.infrastructure import SqlAlchemyUserRepository

from .auth_exceptions import AuthException
from .jwt_utils import decode_access_token, JwtCodecError


_bearer = HTTPBearer(auto_error=False)


def _extract_token_from_request(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials],
) -> Optional[str]:
    """
    Extrae el token JWT de la request en orden de prioridad:
    1. Cookie HTTP-only (para React SPA)
    2. Bearer header (para APIs, mobile, testing)

    Retorna:
    - Token string si se encontró
    - None si no hay token en ninguna fuente
    """
    # --------------------------------------------------------------
    # 1) Intentar cookie HTTP-only (prioridad para SPA)
    # --------------------------------------------------------------
    cookie_token = request.cookies.get(settings.AUTH_COOKIE_NAME)
    if cookie_token:
        return cookie_token

    # --------------------------------------------------------------
    # 2) Fallback a Bearer header (APIs, mobile, testing)
    # --------------------------------------------------------------
    if credentials and credentials.credentials:
        return credentials.credentials

    return None


def token_required_actual(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Dependency fuerte (con DB).

    FUENTES DEL TOKEN:
    - Cookie HTTP-only (para React SPA con credentials: 'include')
    - Bearer header (para APIs, mobile, testing con Authorization header)

    Retorna identity dict estándar:
    - {"user_id": int, "role_id": int, "jti": str}
    """

    # --------------------------------------------------------------
    # 1) Extraer token (cookie o bearer)
    # --------------------------------------------------------------
    token = _extract_token_from_request(request, credentials)

    if not token:
        raise AuthException(code="AUTH_MISSING_TOKEN", http_status=401)

    # --------------------------------------------------------------
    # 2) Validación criptográfica (firma + exp)
    # --------------------------------------------------------------
    try:
        payload = decode_access_token(
            token=token,
            secret_key=settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
    except JwtCodecError:
        raise AuthException(code="AUTH_INVALID_TOKEN", http_status=401)

    # --------------------------------------------------------------
    # 3) Claims mínimos
    # --------------------------------------------------------------
    token_type = payload.get("type")
    sub = payload.get("sub")
    jti = payload.get("jti")

    if token_type != "access":
        raise AuthException(code="AUTH_INVALID_TOKEN_TYPE", http_status=401)

    if not isinstance(sub, dict):
        raise AuthException(code="AUTH_INVALID_SUBJECT", http_status=401)

    user_id = sub.get("user_id")
    if user_id is None:
        raise AuthException(code="AUTH_INVALID_SUBJECT", http_status=401)

    if not jti:
        raise AuthException(code="AUTH_MISSING_JTI", http_status=401)

    # --------------------------------------------------------------
    # 4) Validación DB: usuario + estado + sesión (JTI)
    # --------------------------------------------------------------
    repo = SqlAlchemyUserRepository(db)
    user = repo.get_by_id(int(user_id))

    if user is None:
        raise AuthException(code="AUTH_USER_NOT_FOUND", http_status=401)

    if not user.is_active():
        raise AuthException(
            code="AUTH_USER_NOT_ALLOWED",
            http_status=403,
            meta={"status": user.status},
        )

    if user.token_current_jti is None or user.token_current_jti != str(jti):
        raise AuthException(code="AUTH_SESSION_REVOKED", http_status=401)

    # --------------------------------------------------------------
    # 5) Validación defensiva: rol existe y está activo
    # --------------------------------------------------------------
    # NOTA:
    # - No confiamos en claims del token.
    # - Consultamos roles.is_active real en DB.
    role_row = db.execute(
        text("SELECT is_active FROM roles WHERE id = :role_id LIMIT 1"),
        {"role_id": int(user.role_id)},
    ).mappings().first()

    if role_row is None:
        raise AuthException(code="AUTH_ROLE_NOT_FOUND", http_status=403, meta={"role_id": int(user.role_id)})

    # MySQL devuelve 0/1 (tinyint)
    if int(role_row["is_active"]) != 1:
        raise AuthException(code="AUTH_ROLE_INACTIVE", http_status=403, meta={"role_id": int(user.role_id)})

    # --------------------------------------------------------------
    # 6) Identidad mínima
    # --------------------------------------------------------------
    return {
        "user_id": int(user_id),
        "role_id": int(user.role_id),
        "jti": str(jti),
    }
