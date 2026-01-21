# ======================================================================
# app/common/security/jwt/jwt_dependency.py
# -*- coding: utf-8 -*-
#
# PROPÓSITO:
# - Proveer un mecanismo reutilizable para proteger endpoints REST usando JWT.
#
# POR QUÉ:
# - En FastAPI, el patrón recomendado es Dependency Injection (Depends).
# - Aun así, dejamos un decorador opcional para ergonomía.
#
# RESPONSABILIDAD:
# - Extraer token (Bearer)
# - Validar firma/exp (via jwt_codec)
# - Extraer claims mínimos para construir una identidad de dominio
#
# IMPORTANTE (separación de concerns):
# - Este archivo NO valida contra DB (token_current_jti). Eso es un paso
#   posterior (users module), para no mezclar cross-cutting con infraestructura.
#
# PATRÓN APLICADO:
# - Dependency (FastAPI) + Value Object (JwtIdentity)
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.common.security.jwt.jwt_codec import decode_access_token, JwtCodecError
from app.common.security.jwt.jwt_settings import load_jwt_settings


# ======================================================================
# 1) Esquema Bearer
# ======================================================================
# - auto_error=False para controlar el mensaje y status manualmente.
bearer_scheme = HTTPBearer(auto_error=False)


# ======================================================================
# 2) Value Object: JwtIdentity
# ======================================================================
@dataclass(frozen=True)
class JwtIdentity:
    """
    Identidad mínima extraída del JWT.

    POR QUÉ MÍNIMA:
    - JWT no debe transportar datos sensibles.
    - Solo lo necesario para autorización y trazabilidad.

    CAMPOS:
    - user_id (sub): id del usuario
    - role: rol simple (user/admin)
    - jti: identificador único del token (para revocación posterior vía DB)
    """
    user_id: int
    role: str
    jti: str


# ======================================================================
# 3) Helpers privados
# ======================================================================
def _extract_bearer_token(credentials: Optional[HTTPAuthorizationCredentials]) -> str:
    """
    Extrae el token del header Authorization.

    DECISIÓN:
    - Si no hay token -> 401 (no autenticado)
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )
    return credentials.credentials


# ======================================================================
# 4) Dependency principal: require_jwt_identity
# ======================================================================
def require_jwt_identity(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> JwtIdentity:
    """
    Dependency de FastAPI para proteger endpoints.

    PASOS:
    1) Extraer bearer token.
    2) Cargar settings JWT.
    3) Decodificar y validar token (firma + exp).
    4) Validar claims mínimos (sub, role, jti).
    5) Construir y retornar JwtIdentity.

    NOTA:
    - Aquí solo se valida el token "criptográficamente".
    - La validación de sesión (jti contra DB) va luego en users module.
    """

    # ------------------------------------------------------------------
    # 1) Token del header
    # ------------------------------------------------------------------
    token = _extract_bearer_token(credentials)

    # ------------------------------------------------------------------
    # 2) Settings (centralizados)
    # ------------------------------------------------------------------
    settings = load_jwt_settings()

    # ------------------------------------------------------------------
    # 3) Validación criptográfica (firma + exp)
    # ------------------------------------------------------------------
    try:
        claims = decode_access_token(
            token=token,
            secret_key=settings.secret_key,
            algorithm=settings.algorithm,
        )
    except JwtCodecError:
        # --------------------------------------------------------------
        # Decisión REST:
        # - Token inválido/expirado => 401
        # --------------------------------------------------------------
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    # ------------------------------------------------------------------
    # 4) Claims mínimos esperados
    # - sub: user_id
    # - role: rol
    # - jti: id de token
    # ------------------------------------------------------------------
    sub = claims.get("sub")
    role = claims.get("role")
    jti = claims.get("jti")

    if sub is None or role is None or jti is None:
        # --------------------------------------------------------------
        # Decisión REST:
        # - Token sin claims mínimas => 401
        # --------------------------------------------------------------
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims",
        )

    # ------------------------------------------------------------------
    # 5) Retornar identidad mínima (dominio)
    # ------------------------------------------------------------------
    return JwtIdentity(
        user_id=int(sub),
        role=str(role),
        jti=str(jti),
    )


# ======================================================================
# 5) Decorador opcional: token_required
# ======================================================================
def token_required(endpoint_func):
    """
    Decorador opcional para endpoints.

    NOTA DE DISEÑO:
    - FastAPI se beneficia más de Depends(...) directamente (OpenAPI + DI).
    - Este decorador es solo "azúcar sintáctico" si prefieres @token_required.

    CONTRATO:
    - Inyecta `identity: JwtIdentity` al endpoint.
    """

    def wrapper(
        *args,
        identity: JwtIdentity = Depends(require_jwt_identity),
        **kwargs,
    ):
        return endpoint_func(*args, identity=identity, **kwargs)

    return wrapper