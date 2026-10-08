# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/services/auth/verify_otp_service.py
#
# CASO DE USO:
# - Verificar OTP y finalizar login emitiendo token
#
# REGLAS:
# - OTP inválido/expirado -> fail (sin lockout de cuenta)
# - OTP correcto -> limpiar otp_* (single-use) + token
# - La fuerza bruta se frena en la ruta: rate limit por correo e IP. Con
#   el OTP de 10 min, eso basta y no deja bloquear cuentas ajenas.
#
# SEGURIDAD:
# - Verificación HMAC-SHA256
# - Comparación de tiempo constante (anti timing attacks)
# - Anti-enumeración: correo sin cuenta, sin código activo, vencido o
#   incorrecto responden 401 con el mismo mensaje (ver error_messages).
#   El estado inactivo solo se revela tras un código correcto.
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
        settings: Settings,
    ):
        # --------------------------------------------------------------
        # Dependencias
        # --------------------------------------------------------------
        self._repo = repo
        self._settings = settings

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
            # Anti-enumeration: igual que un código incorrecto.
            return ServiceResult.fail(code="OTP_INVALID", http_status=401)

        # --------------------------------------------------------------
        # 3) "Ahora" del sistema: SIEMPRE UTC-aware (consistente)
        # --------------------------------------------------------------
        now = utc_now()

        # --------------------------------------------------------------
        # 4) Validar que OTP exista
        # --------------------------------------------------------------
        if user.otp_code is None or user.otp_expires_at is None:
            return ServiceResult.fail(code="OTP_NOT_REQUESTED", http_status=401)

        # --------------------------------------------------------------
        # 5) Validar expiración (FIX: normalizar a UTC-aware)
        # --------------------------------------------------------------
        expires_at = ensure_aware_utc(user.otp_expires_at)
        if expires_at is None:
            # Defensivo: si DB viene raro, tratamos como no solicitado
            return ServiceResult.fail(code="OTP_NOT_REQUESTED", http_status=401)

        if expires_at < now:
            return ServiceResult.fail(code="OTP_EXPIRED", http_status=401)

        # --------------------------------------------------------------
        # 6) Validar OTP (HMAC-SHA256)
        # --------------------------------------------------------------
        if not verify_otp_hash(otp_clean, user.otp_code):
            return ServiceResult.fail(code="OTP_INVALID", http_status=401)

        # --------------------------------------------------------------
        # 7) Estado de la cuenta
        # - Se revisa después del código: solo quien demuestra que es
        #   dueño del correo sabe que la cuenta existe y no está activa.
        # --------------------------------------------------------------
        if not user.is_active():
            return ServiceResult.fail(
                code="USER_NOT_ALLOWED",
                http_status=403,
                meta={"status": user.status},
            )

        # --------------------------------------------------------------
        # 8) Éxito: limpiar OTP y emitir token
        # --------------------------------------------------------------
        user.last_login_at = now

        # OTP single-use (importantísimo)
        user.otp_code = None
        user.otp_created_at = None
        user.otp_expires_at = None

        token_pack = create_access_token(
            subject={"user_id": user.id, "role_id": user.role_id},
            secret_key=self._settings.JWT_SECRET_KEY,
            expires_delta=self._settings.JWT_ACCESS_TOKEN_EXPIRES,
            algorithm=self._settings.JWT_ALGORITHM,
        )

        # Revocación fuerte por JTI
        user.token_current_jti = token_pack["jti"]

        self._repo.update(user)
        self._repo.commit()

        return ServiceResult.ok(
            VerifyOtpPayload(
                access_token=token_pack["token"],
                expires_at=token_pack["expires_at"],
                jti=token_pack["jti"],
            )
        )