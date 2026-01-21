# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/services/login_otp_service.py
#
# CASO DE USO:
# - Solicitar OTP para login (solo email).
#
# PATRONES:
# - Application Service Pattern
# - Repository Pattern (UserRepository)
#
# REGLAS (según tus preferencias):
# - Service retorna ServiceResult (ok/fail), NO HTTP.
# - Service NO retorna mensajes de UI (msg/labels).
# - Service retorna datos crudos (incluye códigos de error estables).
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.common.service_result import ServiceResult
from app.common.utils.input_cleaner import clean_email
from app.common.security.otp import generate_numeric_otp, hash_otp_sha1_hex
from app.modules.users.domain import UserRepository


# ======================================================================
# Payload crudo del caso de uso
# ======================================================================

@dataclass(frozen=True)
class LoginOtpPayload:
    """
    Payload crudo (sin formato de presentación).
    """
    email: str
    otp_code: str
    otp_expires_at: datetime


class LoginOtpService:
    """
    Servicio para solicitar OTP.

    Responsabilidad:
    - Validar email (via utils)
    - Verificar usuario y regla de login
    - Generar OTP y persistir hash + expiración
    """

    def __init__(
        self,
        *,
        repo: UserRepository,
        session: Session,
        otp_length: int = 6,
        otp_ttl_minutes: int = 10,
    ):
        self._repo = repo
        self._session = session
        self._otp_length = otp_length
        self._otp_ttl_minutes = otp_ttl_minutes

    def request_login_otp(self, email: str) -> ServiceResult[LoginOtpPayload]:
        """
        Solicita OTP para login.

        Retorna:
        - ok(LoginOtpPayload)
        - fail(code=http_status/meta)  (sin mensajes UI)
        """
        # --------------------------------------------------------------
        # 1) Input cleaning/validation (sin UI)
        # --------------------------------------------------------------
        try:
            email_clean = clean_email(email)
        except ValueError:
            # Mensaje lo decide REST. El service solo entrega el code.
            return ServiceResult.fail(code="VALIDATION_ERROR", http_status=422, meta={"field": "email"})

        # --------------------------------------------------------------
        # 2) Buscar usuario (anti-enumeration)
        # --------------------------------------------------------------
        user = self._repo.get_by_email(email_clean)
        if user is None:
            # No revelamos si existe. Mensaje final lo decide REST.
            return ServiceResult.fail(code="INVALID_REQUEST", http_status=400)

        # --------------------------------------------------------------
        # 3) Regla de negocio: usuario debe poder login
        # --------------------------------------------------------------
        if not user.can_login():
            # Guardamos meta cruda para logs/observabilidad si quieres.
            return ServiceResult.fail(
                code="USER_NOT_ALLOWED",
                http_status=403,
                meta={"status": user.status},
            )

        # --------------------------------------------------------------
        # 4) Generar OTP + expiración (crudo)
        # --------------------------------------------------------------
        otp_plain = generate_numeric_otp(self._otp_length)

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=self._otp_ttl_minutes)

        user.otp_code = hash_otp_sha1_hex(otp_plain)
        user.otp_created_at = now
        user.otp_expires_at = expires_at

        # Persistir
        self._repo.update(user)
        self._session.commit()

        # --------------------------------------------------------------
        # 5) Email (pendiente)
        # --------------------------------------------------------------
        # TODO: enviar correo desde infraestructura (EmailGateway)
        # Por ahora devolvemos otp_plain para desarrollo.
        # --------------------------------------------------------------

        return ServiceResult.ok(
            LoginOtpPayload(
                email=email_clean,
                otp_code=otp_plain,          # TEMPORAL (solo dev)
                otp_expires_at=expires_at,
            )
        )