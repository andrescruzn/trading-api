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
# - Verificación HMAC-SHA256 con soporte legacy SHA1
# - Comparación de tiempo constante (anti timing attacks)
#
# FIX IMPORTANTE (MySQL + SQLAlchemy):
# - MySQL suele devolver datetimes "naive" (sin tzinfo).
# - El sistema calcula `now` como UTC-aware.
# - Comparar naive vs aware rompe.
# - Solución: normalizar fechas desde DB con ensure_aware_utc().
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from app.common.config.settings import Settings
from app.common.contracts import ServiceResult
from app.common.security.jwt import create_access_token
from app.common.security.otp import verify_otp_hash
from app.common.utils import clean_email, clean_str, ensure_aware_utc, utc_now

from app.modules.users.domain import UserRepository


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
            # Anti-enumeration: mantenemos tu decisión actual
            return ServiceResult.fail(code="INVALID_REQUEST", http_status=400)

        # --------------------------------------------------------------
        # 3) "Ahora" del sistema: SIEMPRE UTC-aware (consistente)
        # --------------------------------------------------------------
        now = utc_now()

        # --------------------------------------------------------------
        # 4) Lockout + estado
        # --------------------------------------------------------------
        if user.is_login_locked(now=now):
            # Nota:
            # - user.login_locked_until podría ser naive desde DB
            # - lo normalizamos para no romper isoformat()
            locked_until = ensure_aware_utc(user.login_locked_until)

            return ServiceResult.fail(
                code="LOGIN_LOCKED",
                http_status=429,
                meta={
                    "locked_until": locked_until.isoformat() if locked_until else None
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
        expires_at = ensure_aware_utc(user.otp_expires_at)
        if expires_at is None:
            # Defensivo: si DB viene raro, tratamos como no solicitado
            return ServiceResult.fail(code="OTP_NOT_REQUESTED", http_status=400)

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
        # 7) Validar OTP (HMAC-SHA256 con soporte legacy SHA1)
        # --------------------------------------------------------------
        if not verify_otp_hash(otp_clean, user.otp_code):
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