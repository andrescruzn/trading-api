# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/rest/auth/routes.py
#
# Rutas de autenticación de users:
# - request OTP (login sin password)
#
# RESPONSABILIDAD (REST):
# - Validar schemas (Pydantic)
# - Inyectar dependencias (DB session)
# - Orquestar service + repository
# - Traducir ServiceResult -> HTTP
# - Resolver mensajes de error (presentación)
#
# NOTA ARQUITECTÓNICA:
# - Los Services NO devuelven mensajes de UI.
# - El mapeo code -> msg vive exclusivamente en REST.
# ======================================================================

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.common.http_responder import send
from app.extensions.db import get_db
from app.modules.users.infrastructure import SqlAlchemyUserRepository
from app.modules.users.services import LoginOtpService

from .error_messages import DEFAULT_AUTH_ERROR_MESSAGES
from .schemas import LoginOtpRequest, LoginOtpResponse


# ----------------------------------------------------------------------
# Router del subcontexto auth
# ----------------------------------------------------------------------
router = APIRouter(prefix="/users", tags=["Auth"])


@router.post(
    "/login",
    response_model=LoginOtpResponse,
    status_code=status.HTTP_200_OK,
    # --------------------------------------------------------------
    # Documentación explícita de respuestas de error para Swagger
    # (así deja de salir "Undocumented")
    # --------------------------------------------------------------
    responses={
        400: {"model": LoginOtpResponse, "description": "Bad Request (standard envelope)"},
        403: {"model": LoginOtpResponse, "description": "Forbidden (standard envelope)"},
        422: {"model": LoginOtpResponse, "description": "Validation Error (standard envelope)"},
    },
)
def request_login_otp(
    payload: LoginOtpRequest,
    db: Session = Depends(get_db),
):
    """
    Solicita OTP para login (email).

    Flujo:
    1) REST valida schema
    2) Construye repo + service
    3) Ejecuta caso de uso
    4) Traduce resultado a respuesta HTTP uniforme
    """

    # --------------------------------------------------------------
    # 1) Construcción del caso de uso
    # --------------------------------------------------------------
    repo = SqlAlchemyUserRepository(db)
    service = LoginOtpService(repo=repo, session=db)

    # --------------------------------------------------------------
    # 2) Ejecución del service
    # --------------------------------------------------------------
    result = service.request_login_otp(payload.email)

    # --------------------------------------------------------------
    # 3) ERROR -> contrato estándar
    # --------------------------------------------------------------
    if not result.success:
        err = result.error

        # Fallback defensivo (no debería ocurrir)
        if err is None:
            return send(
                msg="Error",
                status_code=status.HTTP_400_BAD_REQUEST,
                data=[],
            )

        # Mensaje por defecto (presentación) según code
        msg = DEFAULT_AUTH_ERROR_MESSAGES.get(err.code, "Error")

        return send(
            msg=msg,
            status_code=err.http_status,
            data=[],
        )

    # --------------------------------------------------------------
    # 4) OK -> contrato estándar
    # --------------------------------------------------------------
    data = result.data

    # Fallback defensivo
    if data is None:
        return send(
            msg="Error",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            data=[],
        )

    return send(
        msg="OK",
        status_code=status.HTTP_200_OK,
        data={
            "email": data.email,
            "otp_code": data.otp_code,  # TEMPORAL (solo dev)
            "otp_expires_at": data.otp_expires_at.isoformat(),
        },
    )