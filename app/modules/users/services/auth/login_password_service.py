# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/services/auth/login_password_service.py
#
# CASO DE USO:
# - Login por password
#
# REGLAS:
# - Si password incorrecto -> failed_attempts++ y lock 1h al 3er fallo
# - Si password correcto -> reset_failed_attempts() + token + token_current_jti
#
# SEGURIDAD:
# - Anti-enumeration: si no existe usuario, INVALID_CREDENTIALS
# - Password: bcrypt (cost factor 12)
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from app.common.config.settings import Settings
from app.common.contracts import ServiceResult
from app.common.utils.input_cleaner import clean_email, clean_str
from app.common.utils import utc_now
from app.common.security import verify_password
from app.common.security.jwt import create_access_token

from app.modules.users.domain import UserRepository


@dataclass(frozen=True)
class LoginPasswordPayload:
    """
    Payload crudo: token emitido.
    """
    access_token: str
    expires_at: datetime
    jti: str


class LoginPasswordService:
    """
    Service para login por password.
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
        self._repo = repo
        self._session = session
        self._settings = settings
        self._max_failed_attempts = max_failed_attempts
        self._lock_minutes = lock_minutes

    def login(self, email: str, password: str) -> ServiceResult[LoginPasswordPayload]:
        """
        Retorna:
        - ok(LoginPasswordPayload)
        - fail(code, http_status, meta)
        """

        # --------------------------------------------------------------
        # 1) Input cleaning (defensivo)
        # --------------------------------------------------------------
        try:
            email_clean = clean_email(email)
            password_clean = clean_str(password, min_len=1, max_len=255)
        except ValueError:
            return ServiceResult.fail(code="VALIDATION_ERROR", http_status=422)

        # --------------------------------------------------------------
        # 2) Cargar usuario (anti-enumeration)
        # --------------------------------------------------------------
        user = self._repo.get_by_email(email_clean)
        if user is None:
            return ServiceResult.fail(code="INVALID_CREDENTIALS", http_status=401)

        now = utc_now()

        # --------------------------------------------------------------
        # 3) Lockout + estado
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
        # 4) Verificar password (bcrypt)
        # --------------------------------------------------------------
        is_valid = verify_password(password_clean, user.password_hash)

        if not is_valid:
            # Fallo real: incrementa y puede lockear
            user.register_failed_attempt(
                max_attempts=self._max_failed_attempts,
                lock_minutes=self._lock_minutes,
                now=now,
            )
            self._repo.update(user)
            self._session.commit()

            return ServiceResult.fail(code="INVALID_CREDENTIALS", http_status=401)

        # --------------------------------------------------------------
        # 5) Éxito: reset intentos, limpiar OTP y emitir token
        # --------------------------------------------------------------
        user.reset_failed_attempts()
        user.last_login_at = now

        # Evita OTP reusables si el login por password fue exitoso
        user.otp_code = None
        user.otp_created_at = None
        user.otp_expires_at = None

        token_pack = create_access_token(
            subject={"user_id": user.id},
            secret_key=self._settings.JWT_SECRET_KEY,
            expires_delta=self._settings.JWT_ACCESS_TOKEN_EXPIRES,
            algorithm=self._settings.JWT_ALGORITHM,
        )

        # JTI actual => revocación fuerte
        user.token_current_jti = token_pack["jti"]

        self._repo.update(user)
        self._session.commit()

        return ServiceResult.ok(
            LoginPasswordPayload(
                access_token=token_pack["token"],
                expires_at=token_pack["expires_at"],
                jti=token_pack["jti"],
            )
        )