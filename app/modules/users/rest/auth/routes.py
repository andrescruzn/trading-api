# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/rest/auth/routes.py
#
# ENDPOINTS:
# - POST /users/login
#   - con password -> token
#   - sin password -> otp_required
#
# - POST /users/login/otp/verify
#   - valida OTP -> token
#
# - POST /users/logout
#   - requiere Bearer token
#   - revoca sesión (token_current_jti=None)
#
# - POST /users/token/rotate
#   - requiere Bearer token
#   - emite nuevo token y revoca el anterior (nuevo JTI)
#
# RESPONSABILIDAD REST (UI/presentación):
# - Validar schemas (Pydantic)
# - Usar factory para servicios (DI)
# - Usar response_builder para respuestas (presentación)
# - NO meter lógica de negocio aquí
#
# PATRÓN:
# - Factory para DI de servicios
# - Response Builder para construcción de respuestas
# ======================================================================

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.common.http import (
    build_error_response,
    build_internal_error_response,
    build_success_response,
    build_token_response,
    build_otp_required_response,
)
from app.common.security.jwt import token_required_actual
from app.common.security.rate_limiter import check_auth_rate_limit
from app.extensions.db import get_db
from app.modules.users.providers import AuthServiceFactory

from .schemas import (
    LoginRequest,
    LoginResponse,
    VerifyOtpRequest,
    VerifyOtpResponse,
)

# ----------------------------------------------------------------------
# Router principal del submódulo auth dentro de users
# ----------------------------------------------------------------------
router = APIRouter(prefix="/users", tags=["Auth"])


# ----------------------------------------------------------------------
# Dependency para factory de servicios
# ----------------------------------------------------------------------
def get_factory(db: Session = Depends(get_db)) -> AuthServiceFactory:
    """Crea factory de servicios de autenticación."""
    return AuthServiceFactory(session=db)


# ======================================================================
# POST /users/login
# ======================================================================

@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": LoginResponse},
        401: {"model": LoginResponse},
        403: {"model": LoginResponse},
        422: {"model": LoginResponse},
        429: {"model": LoginResponse},
        502: {"model": LoginResponse},
    },
)
def login(
    payload: LoginRequest,
    factory: AuthServiceFactory = Depends(get_factory),
    _rate_limit: None = Depends(check_auth_rate_limit),
):
    """
    Login unificado.

    Flujo:
    1) Si payload.password viene -> valida password -> devuelve token
    2) Si payload.password NO viene -> inicia OTP -> devuelve otp_required
    """
    # ------------------------------------------------------------------
    # 1) Login por password (si viene password)
    # ------------------------------------------------------------------
    if payload.password is not None and payload.password.strip() != "":
        result = factory.login_password().login(payload.email, payload.password)

        if not result.success:
            return build_error_response(result)

        if result.data is None:
            return build_internal_error_response()

        return build_token_response(
            access_token=result.data.access_token,
            expires_at=result.data.expires_at,
        )

    # ------------------------------------------------------------------
    # 2) Login por OTP (si no viene password)
    # ------------------------------------------------------------------
    result = factory.login_otp().request_login_otp(payload.email)

    if not result.success:
        return build_error_response(result)

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
        400: {"model": VerifyOtpResponse},
        401: {"model": VerifyOtpResponse},
        403: {"model": VerifyOtpResponse},
        422: {"model": VerifyOtpResponse},
        429: {"model": VerifyOtpResponse},
    },
)
def verify_otp(
    payload: VerifyOtpRequest,
    factory: AuthServiceFactory = Depends(get_factory),
    _rate_limit: None = Depends(check_auth_rate_limit),
):
    """
    Finaliza login por OTP.

    Flujo:
    1) Valida OTP (hash + expiración)
    2) Si OK -> emite token
    3) Si FAIL -> incrementa failed_attempts y lock al 3er fallo
    """
    result = factory.verify_otp().verify(payload.email, payload.otp_code)

    if not result.success:
        return build_error_response(result)

    if result.data is None:
        return build_internal_error_response()

    return build_token_response(
        access_token=result.data.access_token,
        expires_at=result.data.expires_at,
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
    Logout (revoca sesión actual).

    Reglas:
    - Requiere token válido (firma/exp) + sesión activa (JTI en DB)
    - Al hacer logout: token_current_jti = NULL
      => cualquier token emitido antes queda muerto inmediatamente
    """
    result = factory.logout().logout(user_id=int(identity["user_id"]))

    if not result.success:
        return build_error_response(result)

    return build_success_response()


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
    identity: dict = Depends(token_required_actual),
    factory: AuthServiceFactory = Depends(get_factory),
):
    """
    Rotación de token (refresh simple sin refresh-token separado).

    Requiere:
    - Authorization: Bearer <token válido>

    Efecto:
    - Emite un token nuevo (nuevo JTI)
    - Actualiza DB con nuevo token_current_jti
    - El token anterior queda inválido inmediatamente
    """
    result = factory.rotate_token().rotate(user_id=int(identity["user_id"]))

    if not result.success:
        return build_error_response(result)

    if result.data is None:
        return build_internal_error_response()

    return build_token_response(
        access_token=result.data.access_token,
        expires_at=result.data.expires_at,
    )
