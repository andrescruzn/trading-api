# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/services/auth/login_otp_service.py
#
# CASO DE USO:
# - Solicitar OTP para login (inicio de flujo OTP).
#
# SEGURIDAD:
# - Si login está bloqueado -> fail LOGIN_LOCKED
# - Pedir OTP NO incrementa failed_attempts (no es fallo de auth)
# - Persistimos OTP hasheado (nunca OTP plano)
#
# DECISIÓN DE CONSISTENCIA (anti-errores):
# - Persistimos OTP (commit) antes de enviar email, para que el OTP
#   "exista" realmente si el usuario lo recibe.
# - Si el envío falla, limpiamos OTP y hacemos commit (rollback lógico).
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.common.config.settings import Settings
from app.common.contracts import ServiceResult
from app.common.utils.input_cleaner import clean_email
from app.common.security.otp import generate_numeric_otp, hash_otp_sha1_hex

from app.modules.mailer.domain import OTP_TEMPLATE
from app.modules.mailer.services import MailerService
from app.modules.users.domain import UserRepository


@dataclass(frozen=True)
class LoginOtpPayload:
    """
    Payload crudo del caso de uso (sin UI).
    """
    email: str
    otp_expires_at: datetime
    otp_code: Optional[str] = None  # Solo development


class LoginOtpService:
    """
    Service para iniciar login por OTP.
    """

    def __init__(
        self,
        *,
        repo: UserRepository,
        session: Session,
        settings: Settings,
        mailer: MailerService,
        otp_length: int = 6,
        otp_ttl_minutes: int = 10,
    ):
        # --------------------------------------------------------------
        # Dependencias
        # --------------------------------------------------------------
        self._repo = repo
        self._session = session
        self._settings = settings
        self._mailer = mailer

        # --------------------------------------------------------------
        # Parámetros de negocio (OTP)
        # --------------------------------------------------------------
        self._otp_length = otp_length
        self._otp_ttl_minutes = otp_ttl_minutes

    def request_login_otp(self, email: str) -> ServiceResult[LoginOtpPayload]:
        """
        Retorna:
        - ok(LoginOtpPayload)
        - fail(code, http_status, meta)
        """

        # --------------------------------------------------------------
        # 1) Input cleaning (defensivo)
        # --------------------------------------------------------------
        try:
            email_clean = clean_email(email)
        except ValueError:
            return ServiceResult.fail(
                code="VALIDATION_ERROR",
                http_status=422,
                meta={"field": "email"},
            )

        # --------------------------------------------------------------
        # 2) Buscar usuario (anti-enumeration)
        # --------------------------------------------------------------
        user = self._repo.get_by_email(email_clean)
        if user is None:
            # Nota:
            # - No decimos "no existe"; devolvemos code estable.
            return ServiceResult.fail(code="INVALID_REQUEST", http_status=400)

        now = datetime.now(timezone.utc)

        # --------------------------------------------------------------
        # 3) Lockout + estado (reglas de dominio)
        # --------------------------------------------------------------
        if user.is_login_locked(now=now):
            return ServiceResult.fail(
                code="LOGIN_LOCKED",
                http_status=429,
                meta={
                    "locked_until": user.login_locked_until.isoformat()
                    if user.login_locked_until
                    else None
                },
            )

        if not user.is_active():
            return ServiceResult.fail(
                code="USER_NOT_ALLOWED",
                http_status=403,
                meta={"status": user.status},
            )

        # --------------------------------------------------------------
        # 4) Generar OTP y expiración
        # --------------------------------------------------------------
        otp_plain = generate_numeric_otp(self._otp_length)
        expires_at = now + timedelta(minutes=self._otp_ttl_minutes)

        # --------------------------------------------------------------
        # 5) Persistir OTP hasheado (commit)
        # - Garantiza consistencia si el usuario recibe el código.
        # --------------------------------------------------------------
        user.otp_code = hash_otp_sha1_hex(otp_plain)
        user.otp_created_at = now
        user.otp_expires_at = expires_at

        self._repo.update(user)
        self._session.commit()

        # --------------------------------------------------------------
        # 6) Enviar correo
        # --------------------------------------------------------------
        mail_result = self._mailer.send_by_template(
            to_email=email_clean,
            template=OTP_TEMPLATE,
            context={
                "otp_code": otp_plain,
                "expires_minutes": self._otp_ttl_minutes,
                "title": "OTP Trading AI",
            },
            text_body=f"Tu OTP es: {otp_plain}. Expira en {self._otp_ttl_minutes} minutos.",
        )

        if not mail_result.success:
            # ----------------------------------------------------------
            # Rollback lógico:
            # - Si el correo falla, NO puede quedar OTP activo.
            # ----------------------------------------------------------
            user.otp_code = None
            user.otp_created_at = None
            user.otp_expires_at = None

            self._repo.update(user)
            self._session.commit()

            return ServiceResult.fail(
                code="OTP_EMAIL_SEND_FAILED",
                http_status=502,
                meta={"provider": "smtp"},
            )

        # --------------------------------------------------------------
        # 7) Respuesta (solo dev devuelve otp_code)
        # --------------------------------------------------------------
        otp_for_debug = otp_plain if self._settings.APP_ENV == "development" else None

        return ServiceResult.ok(
            LoginOtpPayload(
                email=email_clean,
                otp_expires_at=expires_at,
                otp_code=otp_for_debug,
            )
        )