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
# RESPONSABILIDAD REST:
# - Validar schemas (Pydantic)
# - Instanciar repo + services (DI manual)
# - Traducir ServiceResult -> send()
# - No meter lógica de negocio aquí
# ======================================================================

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.common.config import settings
from app.common.http import send
from app.common.security.jwt import token_required_actual
from app.extensions.db import get_db
from app.modules.mailer.providers import build_mailer  # ✅ FIX: factory DI para MailerService
from app.modules.users.infrastructure import SqlAlchemyUserRepository
from app.modules.users.services.auth import (
    LoginOtpService,
    LoginPasswordService,
    VerifyOtpService,
    LogoutService,
    RotateTokenService,
)

from .error_messages import DEFAULT_AUTH_ERROR_MESSAGES
from .schemas import (
    LoginRequest,
    LoginResponse,
    VerifyOtpRequest,
    VerifyOtpResponse,
)

router = APIRouter(prefix="/users", tags=["Auth"])


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
    db: Session = Depends(get_db),
):
    """
    Login unificado.

    Flujo:
    1) Si payload.password viene:
       - valida password
       - devuelve token
    2) Si payload.password NO viene:
       - inicia OTP (envía correo)
       - devuelve otp_required=true + otp_expires_at
    """

    # --------------------------------------------------------------
    # Repo (infra) para el módulo users
    # --------------------------------------------------------------
    repo = SqlAlchemyUserRepository(db)

    # --------------------------------------------------------------
    # 1) Login por password (si viene password)
    # --------------------------------------------------------------
    if payload.password is not None and payload.password.strip() != "":
        service = LoginPasswordService(
            repo=repo,
            session=db,
            settings=settings,
            max_failed_attempts=3,
            lock_minutes=60,
        )

        result = service.login(payload.email, payload.password)

        if not result.success:
            err = result.error
            msg = DEFAULT_AUTH_ERROR_MESSAGES.get(err.code, "Error") if err else "Error"
            return send(msg=msg, status_code=(err.http_status if err else 400), data=[])

        data = result.data
        if data is None:
            return send(msg="Error", status_code=500, data=[])

        return send(
            msg="OK",
            status_code=200,
            data={
                "access_token": data.access_token,
                "token_type": "bearer",
                "expires_at": data.expires_at.isoformat(),
            },
        )

    # --------------------------------------------------------------
    # 2) Login por OTP (si no viene password)
    # --------------------------------------------------------------
    # ✅ FIX:
    # - MailerService requiere mail_client + template_renderer.
    # - build_mailer() arma esos adaptadores (SMTP + Jinja) y retorna el service listo.
    mailer = build_mailer(settings)

    otp_service = LoginOtpService(
        repo=repo,
        session=db,
        settings=settings,
        mailer=mailer,
        otp_length=6,
        otp_ttl_minutes=10,
    )

    result = otp_service.request_login_otp(payload.email)

    if not result.success:
        err = result.error
        msg = DEFAULT_AUTH_ERROR_MESSAGES.get(err.code, "Error") if err else "Error"
        return send(msg=msg, status_code=(err.http_status if err else 400), data=[])

    data = result.data
    if data is None:
        return send(msg="Error", status_code=500, data=[])

    return send(
        msg="OK",
        status_code=200,
        data={
            "otp_required": True,
            "email": data.email,
            "otp_expires_at": data.otp_expires_at.isoformat(),
            "otp_code": data.otp_code,  # solo dev
        },
    )


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
    db: Session = Depends(get_db),
):
    """
    Finaliza login por OTP.

    Flujo:
    1) valida OTP (hash + expiración)
    2) si OK -> emite token
    3) si FAIL -> incrementa failed_attempts y lock al 3er fallo
    """

    repo = SqlAlchemyUserRepository(db)

    service = VerifyOtpService(
        repo=repo,
        session=db,
        settings=settings,
        max_failed_attempts=3,
        lock_minutes=60,
    )

    result = service.verify(payload.email, payload.otp_code)

    if not result.success:
        err = result.error
        msg = DEFAULT_AUTH_ERROR_MESSAGES.get(err.code, "Error") if err else "Error"
        return send(msg=msg, status_code=(err.http_status if err else 400), data=[])

    data = result.data
    if data is None:
        return send(msg="Error", status_code=500, data=[])

    return send(
        msg="OK",
        status_code=200,
        data={
            "access_token": data.access_token,
            "token_type": "bearer",
            "expires_at": data.expires_at.isoformat(),
        },
    )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
)
def logout(
    identity: dict = Depends(token_required_actual),  # ✅ candado + exige Authorization: Bearer <token>
    db: Session = Depends(get_db),
):
    """
    Logout (revoca sesión actual).

    Reglas:
    - Requiere token válido (firma/exp) + sesión activa (JTI en DB)
    - Al hacer logout: token_current_jti = NULL
      => cualquier token emitido antes queda muerto inmediatamente.
    """

    repo = SqlAlchemyUserRepository(db)
    service = LogoutService(repo=repo, session=db)

    result = service.logout(user_id=int(identity["user_id"]))

    if not result.success:
        err = result.error
        msg = DEFAULT_AUTH_ERROR_MESSAGES.get(err.code, "Error") if err else "Error"
        return send(msg=msg, status_code=(err.http_status if err else 400), data=[])

    return send(msg="OK", status_code=200, data=[])


@router.post(
    "/token/rotate",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": LoginResponse},
        403: {"model": LoginResponse},
    },
)
def rotate_token(
    identity: dict = Depends(token_required_actual),  # ✅ candado + exige Authorization: Bearer <token>
    db: Session = Depends(get_db),
):
    """
    Rotación de token (refresh simple sin refresh-token separado).

    Requiere:
    - Authorization: Bearer <token válido>

    Efecto:
    - Emite un token nuevo (nuevo JTI)
    - Actualiza DB con nuevo token_current_jti
    - El token anterior queda inválido inmediatamente.
    """

    repo = SqlAlchemyUserRepository(db)

    service = RotateTokenService(
        repo=repo,
        session=db,
        settings=settings,
    )

    result = service.rotate(user_id=int(identity["user_id"]))

    if not result.success:
        err = result.error
        msg = DEFAULT_AUTH_ERROR_MESSAGES.get(err.code, "Error") if err else "Error"
        return send(msg=msg, status_code=(err.http_status if err else 400), data=[])

    data = result.data
    if data is None:
        return send(msg="Error", status_code=500, data=[])

    return send(
        msg="OK",
        status_code=200,
        data={
            "access_token": data.access_token,
            "token_type": "bearer",
            "expires_at": data.expires_at.isoformat(),
        },
    )