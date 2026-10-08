# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/services/auth/login_otp_service.py
#
# CASO DE USO:
# - Solicitar OTP para login (inicio de flujo OTP).
#
# SEGURIDAD:
# - Anti-enumeración: si el correo no tiene cuenta o la cuenta no está
#   activa, respondemos igual que en el éxito (misma forma, misma
#   expiración) pero sin generar OTP ni enviar correo. La UI avanza al
#   paso del código en todos los casos.
# - Sin lockout de cuenta: el abuso se frena con rate limit por correo e
#   IP en la ruta (ver rate_limiter.py).
# - Persistimos OTP hasheado con HMAC-SHA256 (nunca OTP plano)
#
# ENVÍO EN SEGUNDO PLANO:
# - Persistimos OTP (commit) y encolamos el correo: la respuesta no espera
#   al SMTP, así que tarda lo mismo exista o no la cuenta y nunca falla
#   por el proveedor de correo.
# - Si el envío falla tras los reintentos, queda en el log; el OTP vence
#   solo a los 10 min y la persona puede pedir otro.
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from app.common.config.settings import Settings
from app.common.contracts import ServiceResult
from app.common.utils.input_cleaner import clean_email
from app.common.security.otp import generate_numeric_otp, hash_otp

from app.modules.mailer.domain import OTP_TEMPLATE
from app.modules.mailer.services import MailerService
from app.common.utils import utc_now
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
        settings: Settings,
        mailer: MailerService,
        otp_length: int = 6,
        otp_ttl_minutes: int = 10,
    ):
        # --------------------------------------------------------------
        # Dependencias
        # --------------------------------------------------------------
        self._repo = repo
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

        now = utc_now()

        # --------------------------------------------------------------
        # 2) Buscar usuario (anti-enumeration)
        # - Sin cuenta: misma respuesta que el éxito, sin OTP ni correo.
        # --------------------------------------------------------------
        user = self._repo.get_by_email(email_clean)
        if user is None:
            return self._silent_ok(email_clean, now)

        # --------------------------------------------------------------
        # 3) Estado
        # --------------------------------------------------------------
        if not user.is_active():
            # Anti-enumeration: no confirmamos que la cuenta existe.
            return self._silent_ok(email_clean, now)

        # --------------------------------------------------------------
        # 4) Generar OTP y expiración
        # --------------------------------------------------------------
        otp_plain = generate_numeric_otp(self._otp_length)
        expires_at = now + timedelta(minutes=self._otp_ttl_minutes)

        # --------------------------------------------------------------
        # 5) Persistir OTP hasheado (commit)
        # - Garantiza consistencia si el usuario recibe el código.
        # --------------------------------------------------------------
        user.otp_code = hash_otp(otp_plain)
        user.otp_created_at = now
        user.otp_expires_at = expires_at

        self._repo.update(user)
        self._repo.commit()

        # --------------------------------------------------------------
        # 6) Encolar correo (segundo plano, con reintentos)
        # --------------------------------------------------------------
        self._mailer.send_by_template_in_background(
            to_email=email_clean,
            template=OTP_TEMPLATE,
            context={
                "otp_code": otp_plain,
                "expires_minutes": self._otp_ttl_minutes,
                "title": "Tu código de acceso a Trading App",
            },
            text_body=f"Tu OTP es: {otp_plain}. Expira en {self._otp_ttl_minutes} minutos.",
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

    def _silent_ok(self, email: str, now: datetime) -> ServiceResult[LoginOtpPayload]:
        """
        Respuesta indistinguible del éxito para correos sin cuenta activa.

        - No persiste nada ni envía correo.
        - Nunca incluye otp_code (no existe).
        """
        return ServiceResult.ok(
            LoginOtpPayload(
                email=email,
                otp_expires_at=now + timedelta(minutes=self._otp_ttl_minutes),
            )
        )
