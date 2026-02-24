# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/rest/auth/routes.py
#
# ENDPOINTS:
# - POST /users/login
# - POST /users/login/otp/verify
# - POST /users/logout
# - POST /users/token/rotate
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
from app.common.security.rate_limiter import check_auth_rate_limit
from app.extensions.db import get_db
from app.modules.users.providers import AuthServiceFactory

from .schemas import (
    LoginRequest,
    LoginResponse,
    VerifyOtpRequest,
    VerifyOtpResponse,
    UserProfileResponse,
    ChangePasswordRequest,
    ChangePasswordResponse,
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
    response: Optional[str] = Query(
        default=None,
        description="Tipo de respuesta: omitir para cookie, 'token' para JSON",
        examples=["token"],
    ),
    factory: AuthServiceFactory = Depends(get_factory),
    _rate_limit: None = Depends(check_auth_rate_limit),
):
    """
    Login unificado.

    **Bandera `?response=token`:**
    - Sin bandera → Cookie HTTP-only (para React)
    - `?response=token` → Token en body (para Postman/Swagger/móvil)

    **Flujo:**
    1. Si viene password → valida → respuesta según bandera
    2. Si NO viene password → inicia OTP → devuelve otp_required
    """
    # ------------------------------------------------------------------
    # 1) Login por password
    # ------------------------------------------------------------------
    if payload.password is not None and payload.password.strip() != "":
        result = factory.login_password().login(payload.email, payload.password)

        if not result.success:
            return build_error_response(result)

        if result.data is None:
            return build_internal_error_response()

        return _build_auth_response(
            access_token=result.data.access_token,
            expires_at=result.data.expires_at,
            response_type=response,
        )

    # ------------------------------------------------------------------
    # 2) Login por OTP
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
    result = factory.verify_otp().verify(payload.email, payload.otp_code)

    if not result.success:
        return build_error_response(result)

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
        return build_error_response(result)

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
# PATCH /users/me/password
# ======================================================================

@router.patch(
    "/me/password",
    response_model=ChangePasswordResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ChangePasswordResponse},
        422: {"model": ChangePasswordResponse},
    },
)
def change_password(
    payload: ChangePasswordRequest,
    identity: dict = Depends(token_required_actual),
    factory: AuthServiceFactory = Depends(get_factory),
):
    """
    Cambiar la contraseña del usuario autenticado.

    - Verifica la contraseña actual.
    - Valida política de seguridad (8+ chars, mayúscula, minúscula, número).
    - Al cambiar con éxito: revoca la sesión actual (requiere nuevo login).
    """
    result = factory.change_password().change(
        user_id=int(identity["user_id"]),
        current_password=payload.current_password,
        new_password=payload.new_password,
    )

    if not result.success:
        # Sin AUTH_ERROR_MESSAGES: json.msg llega como código crudo
        # ("PASSWORD_TOO_WEAK", "INVALID_CREDENTIALS", etc.) para que
        # el JS del frontend lo mapee a mensajes en español.
        return build_error_response(result)

    # Limpiar cookie: el JTI fue revocado en DB, pero el browser
    # aún tiene la cookie. Si no la borramos aquí, /login la ve
    # como válida (JWT signature ok) y redirige a /dashboard → loop.
    response = JSONResponse(
        status_code=200,
        content={
            "msg": "Password changed successfully",
            "errorCode": 200,
            "data": {"password_changed": True},
        },
    )
    response.delete_cookie(
        key=settings.AUTH_COOKIE_NAME,
        path=settings.AUTH_COOKIE_PATH,
        domain=settings.AUTH_COOKIE_DOMAIN,
        secure=settings.AUTH_COOKIE_SECURE,
        httponly=True,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )
    return response


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
        return build_error_response(result)

    if result.data is None:
        return build_internal_error_response()

    return _build_auth_response(
        access_token=result.data.access_token,
        expires_at=result.data.expires_at,
        response_type=response,
    )
