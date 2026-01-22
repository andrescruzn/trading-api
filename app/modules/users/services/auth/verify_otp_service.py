# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/services/auth/verify_otp_service.py
#
# CASO DE USO:
# - Verificar OTP y finalizar login emitiendo token
#
# REGLAS:
# - OTP inválido/expirado -> failed_attempts++ y lock 1h al 3er fallo
# - OTP correcto -> reset_failed_attempts() + limpiar otp_* + token
#
# SEGURIDAD:
# - Comparación de hashes con compare_digest (anti timing)
#
# FIX IMPORTANTE (MySQL + SQLAlchemy):
# - MySQL suele devolver TIMESTAMP como datetime "naive" (sin tzinfo).
# - Nosotros calculamos `now` como datetime "aware" (UTC).
# - Comparar naive vs aware lanza:
#   TypeError: can't compare offset-naive and offset-aware datetimes
# - Solución: normalizar fechas del usuario a UTC-aware antes de comparar.
# ======================================================================

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.common.config.settings import Settings
from app.common.contracts import ServiceResult
from app.common.security.jwt import create_access_token
from app.common.security.otp import hash_otp_sha1_hex
from app.common.utils.input_cleaner import clean_email, clean_str

from app.modules.users.domain import UserRepository


# ----------------------------------------------------------------------
# Helper: normalización TZ
# ----------------------------------------------------------------------
def _as_utc_aware(dt: datetime) -> datetime:
    """
    Normaliza un datetime a UTC "aware".

    Regla:
    - Si dt viene naive (sin tzinfo), asumimos que representa UTC.
      (Esto es consistente con el resto del proyecto: tokens/servicios trabajan en UTC)
    - Si dt viene aware, lo convertimos a UTC.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


@dataclass(frozen=True)
class VerifyOtpPayload:
    """
    Payload crudo: token emitido por OTP.
    """
    access_token: str
    expires_at: datetime
    jti: str


class VerifyOtpService:
    """
    Service para validar OTP y emitir token.
    """

    def __init__(
        self,
        *,
        repo: UserRepository,
        session: Session,
        settings: Settings,
        max_failed_attempts: int = 3,
        lock_minutes: int = 60,
    ):
        # --------------------------------------------------------------
        # Dependencias
        # --------------------------------------------------------------
        self._repo = repo
        self._session = session
        self._settings = settings

        # --------------------------------------------------------------
        # Parámetros de seguridad / lockout
        # --------------------------------------------------------------
        self._max_failed_attempts = max_failed_attempts
        self._lock_minutes = lock_minutes

    def verify(self, email: str, otp_code: str) -> ServiceResult[VerifyOtpPayload]:
        """
        Retorna:
        - ok(VerifyOtpPayload)
        - fail(code, http_status, meta)
        """

        # --------------------------------------------------------------
        # 1) Input cleaning (defensivo)
        # --------------------------------------------------------------
        try:
            email_clean = clean_email(email)
            otp_clean = clean_str(otp_code, min_len=4, max_len=12)
        except ValueError:
            return ServiceResult.fail(code="VALIDATION_ERROR", http_status=422)

        # --------------------------------------------------------------
        # 2) Cargar usuario
        # --------------------------------------------------------------
        user = self._repo.get_by_email(email_clean)
        if user is None:
            # Anti-enumeration: puedes mantener INVALID_REQUEST como ya lo tienes
            return ServiceResult.fail(code="INVALID_REQUEST", http_status=400)

        # --------------------------------------------------------------
        # 3) "Ahora" del sistema: SIEMPRE UTC-aware (consistente)
        # --------------------------------------------------------------
        now = datetime.now(timezone.utc)

        # --------------------------------------------------------------
        # 4) Lockout + estado
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
        # 5) Validar que OTP exista
        # --------------------------------------------------------------
        if user.otp_code is None or user.otp_expires_at is None:
            return ServiceResult.fail(code="OTP_NOT_REQUESTED", http_status=400)

        # --------------------------------------------------------------
        # 6) Validar expiración (FIX: normalizar a UTC-aware)
        # --------------------------------------------------------------
        expires_at = _as_utc_aware(user.otp_expires_at)

        if expires_at < now:
            # Fallo real: cuenta para lockout
            user.register_failed_attempt(
                max_attempts=self._max_failed_attempts,
                lock_minutes=self._lock_minutes,
                now=now,
            )
            self._repo.update(user)
            self._session.commit()

            return ServiceResult.fail(code="OTP_EXPIRED", http_status=401)

        # --------------------------------------------------------------
        # 7) Validar OTP por hash (compare_digest anti-timing)
        # --------------------------------------------------------------
        provided_hash = hash_otp_sha1_hex(otp_clean)

        if not secrets.compare_digest(provided_hash, user.otp_code):
            user.register_failed_attempt(
                max_attempts=self._max_failed_attempts,
                lock_minutes=self._lock_minutes,
                now=now,
            )
            self._repo.update(user)
            self._session.commit()

            return ServiceResult.fail(code="OTP_INVALID", http_status=401)

        # --------------------------------------------------------------
        # 8) Éxito: limpiar OTP, reset intentos y emitir token
        # --------------------------------------------------------------
        user.reset_failed_attempts()
        user.last_login_at = now

        # OTP single-use (importantísimo)
        user.otp_code = None
        user.otp_created_at = None
        user.otp_expires_at = None

        token_pack = create_access_token(
            subject={"user_id": user.id},
            secret_key=self._settings.JWT_SECRET_KEY,
            expires_delta=self._settings.JWT_ACCESS_TOKEN_EXPIRES,
            algorithm=self._settings.JWT_ALGORITHM,
        )

        # Revocación fuerte por JTI
        user.token_current_jti = token_pack["jti"]

        self._repo.update(user)
        self._session.commit()

        return ServiceResult.ok(
            VerifyOtpPayload(
                access_token=token_pack["token"],
                expires_at=token_pack["expires_at"],
                jti=token_pack["jti"],
            )
        )