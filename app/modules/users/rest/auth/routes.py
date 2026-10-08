# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/rest/auth/routes.py
#
# ENDPOINTS:
# - POST /users/login            (pide el código OTP por correo)
# - POST /users/login/otp/verify (verifica el código y abre sesión)
# - POST /users/logout
# - GET  /users/me
# - POST /users/token/rotate
#
# LOGIN SOLO POR OTP:
# - No hay contraseñas: el único método de acceso es el código de un solo
#   uso que llega al correo.
#
# BANDERA ?response=token:
# - Sin bandera (default) → Cookie HTTP-only (React SPA)
# - Con ?response=token   → Token en body JSON (Postman/Swagger/móvil)
#
# SEGURIDAD:
# - El guard acepta token desde cookie O header Bearer.
# - Cookies HTTP-only protegen contra XSS.
# - Bearer header para clientes sin soporte de cookies.
# ======================================================================

from __future__ import annotations

from typing import Optional, Union

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.common.config import settings
from app.common.errors import AUTH_ERROR_MESSAGES
from app.modules.users.rest.auth.error_messages import OTP_VERIFY_ERROR_MESSAGES
from app.common.http import (
    build_error_response,
    build_internal_error_response,
    build_otp_required_response,
    build_cookie_auth_response,
    build_logout_response,
    build_token_response,
    build_success_response,
)
from app.common.security.jwt import token_required_actual
from app.common.security.rate_limiter import (
    check_auth_rate_limit,
    check_email_rate_limit,
    otp_request_rate_limiter,
    otp_verify_rate_limiter,
)
from app.extensions.db import get_db
from app.modules.users.providers import AuthServiceFactory

from .schemas import (
    LoginRequest,
    LoginResponse,
    VerifyOtpRequest,
    VerifyOtpResponse,
    UserProfileResponse,
)

# ----------------------------------------------------------------------
# Router
# ----------------------------------------------------------------------
router = APIRouter(prefix="/users", tags=["Auth"])


# ----------------------------------------------------------------------
# Dependencies
# ----------------------------------------------------------------------
def get_factory(db: Session = Depends(get_db)) -> AuthServiceFactory:
    """Crea factory de servicios de autenticación."""
    return AuthServiceFactory(session=db)


def _get_cookie_max_age() -> int:
    """Max-age de cookie sincronizado con JWT TTL."""
    return int(settings.JWT_ACCESS_TOKEN_EXPIRES.total_seconds())


# ----------------------------------------------------------------------
# Helper: construir respuesta según bandera
# ----------------------------------------------------------------------
def _build_auth_response(
    access_token: str,
    expires_at,
    response_type: Optional[str],
) -> Union[JSONResponse, dict]:
    """
    Construye respuesta de autenticación según bandera.

    - response_type=None (default) → Cookie HTTP-only
    - response_type="token"        → Token en body JSON
    """
    if response_type == "token":
        # Postman/Swagger/móvil: devolver token en body
        return build_token_response(
            access_token=access_token,
            expires_at=expires_at,
        )

    # React SPA: setear cookie HTTP-only
    return build_cookie_auth_response(
        access_token=access_token,
        expires_at=expires_at,
        max_age_seconds=_get_cookie_max_age(),
    )


# ======================================================================
# POST /users/login
# ======================================================================

@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    responses={
        422: {"model": LoginResponse},
        429: {"model": LoginResponse},
    },
)
def login(
    payload: LoginRequest,
    factory: AuthServiceFactory = Depends(get_factory),
    _rate_limit: None = Depends(check_auth_rate_limit),
):
    """
    Paso 1 del login: envía un código OTP al correo.

    Anti-enumeración: responde igual exista o no la cuenta (solo se envía
    el correo si existe y está activa). El correo sale en segundo plano.

    Rate limit: por IP y por correo (3 códigos cada 10 min) → 429.

    Devuelve `otp_required` con la expiración del código. La sesión se abre
    en `POST /users/login/otp/verify`.
    """
    check_email_rate_limit(otp_request_rate_limiter, payload.email)

    result = factory.login_otp().request_login_otp(payload.email)

    if not result.success:
        return build_error_response(result, AUTH_ERROR_MESSAGES)

    if result.data is None:
        return build_internal_error_response()

    return build_otp_required_response(
        email=result.data.email,
        otp_expires_at=result.data.otp_expires_at,
        otp_code=result.data.otp_code,
    )


# ======================================================================
# POST /users/login/otp/verify
# ======================================================================

@router.post(
    "/login/otp/verify",
    response_model=VerifyOtpResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": VerifyOtpResponse},
        403: {"model": VerifyOtpResponse},
        422: {"model": VerifyOtpResponse},
        429: {"model": VerifyOtpResponse},
    },
)
def verify_otp(
    payload: VerifyOtpRequest,
    response: Optional[str] = Query(
        default=None,
        description="Tipo de respuesta: omitir para cookie, 'token' para JSON",
        examples=["token"],
    ),
    factory: AuthServiceFactory = Depends(get_factory),
    _rate_limit: None = Depends(check_auth_rate_limit),
):
    """
    Verificar OTP y completar login.

    **Bandera `?response=token`:**
    - Sin bandera → Cookie HTTP-only (para React)
    - `?response=token` → Token en body (para Postman/Swagger/móvil)
    """
    # Sin lockout de cuenta: 5 intentos por correo cada 10 min (+ por IP).
    check_email_rate_limit(otp_verify_rate_limiter, payload.email)

    result = factory.verify_otp().verify(payload.email, payload.otp_code)

    if not result.success:
        return build_error_response(result, OTP_VERIFY_ERROR_MESSAGES)

    if result.data is None:
        return build_internal_error_response()

    return _build_auth_response(
        access_token=result.data.access_token,
        expires_at=result.data.expires_at,
        response_type=response,
    )


# ======================================================================
# POST /users/logout
# ======================================================================

@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
)
def logout(
    identity: dict = Depends(token_required_actual),
    factory: AuthServiceFactory = Depends(get_factory),
):
    """
    Logout (revoca sesión).

    - Acepta token desde cookie O header Bearer.
    - Invalida token en DB (token_current_jti = NULL).
    - Limpia cookie si existe.
    """
    result = factory.logout().logout(user_id=int(identity["user_id"]))

    if not result.success:
        return build_error_response(result, AUTH_ERROR_MESSAGES)

    return build_logout_response()


# ======================================================================
# GET /users/me
# ======================================================================

@router.get(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": UserProfileResponse},
        403: {"model": UserProfileResponse},
        404: {"model": UserProfileResponse},
    },
)
def get_me(
    identity: dict = Depends(token_required_actual),
    factory: AuthServiceFactory = Depends(get_factory),
):
    """
    Obtener el perfil del usuario autenticado.

    Retorna datos del usuario actual extraídos del token JWT.
    Útil para cargar el dashboard y verificar el estado de la sesión.
    """
    result = factory.get_me().get(user_id=int(identity["user_id"]))

    if not result.success:
        return build_error_response(result, AUTH_ERROR_MESSAGES)

    if result.data is None:
        return build_internal_error_response()

    profile = result.data

    return build_success_response(
        data={
            "id": profile.id,
            "email": profile.email,
            "full_name": profile.full_name,
            "role_id": profile.role_id,
            "role_code": profile.role_code,   # "user" | "admin"
            "role_label": profile.role_name,  # "Usuario" | "Administrador" (desde BD)
            "status": profile.status,
            "last_login_at": profile.last_login_at.isoformat() if profile.last_login_at else None,
            "created_at": profile.created_at.isoformat() if profile.created_at else None,
        },
        msg="OK",
    )


# ======================================================================
# POST /users/token/rotate
# ======================================================================

@router.post(
    "/token/rotate",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": LoginResponse},
        403: {"model": LoginResponse},
    },
)
def rotate_token(
    response: Optional[str] = Query(
        default=None,
        description="Tipo de respuesta: omitir para cookie, 'token' para JSON",
        examples=["token"],
    ),
    identity: dict = Depends(token_required_actual),
    factory: AuthServiceFactory = Depends(get_factory),
):
    """
    Rotar token (emitir nuevo, invalidar anterior).

    **Bandera `?response=token`:**
    - Sin bandera → Cookie HTTP-only (para React)
    - `?response=token` → Token en body (para Postman/Swagger/móvil)
    """
    result = factory.rotate_token().rotate(user_id=int(identity["user_id"]))

    if not result.success:
        return build_error_response(result, AUTH_ERROR_MESSAGES)

    if result.data is None:
        return build_internal_error_response()

    return _build_auth_response(
        access_token=result.data.access_token,
        expires_at=result.data.expires_at,
        response_type=response,
    )
