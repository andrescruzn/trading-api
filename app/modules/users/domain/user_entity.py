# app/modules/users/domain/user_entity.py
# -*- coding: utf-8 -*-

# ======================================================================
# User Domain Entity
# ----------------------------------------------------------------------
# Representa un usuario del sistema desde el punto de vista del dominio.
# No depende de framework, ORM ni infraestructura.
#
# CAMBIOS CLAVE (seguridad):
# - role_id: int  (FK a roles.id)
# - login_locked_until: datetime | None
# - Reglas: si supera N intentos fallidos, se bloquea por X minutos.
#
# NOTA:
# - El dominio define reglas puras (sin DB, sin HTTP, sin UI).
# - El cálculo de "ahora" lo recibe como argumento para testear fácil.
# ======================================================================

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from app.common.utils import ensure_aware_utc, utc_now



class User:
    """
    Entidad de dominio: User

    Responsabilidad:
    - Modelar el usuario y su estado de autenticación
    - Encapsular reglas base de acceso (activo, lockout, etc.)
    """

    def __init__(
        self,
        id: int,
        email: str,
        password_hash: str,
        role_id: int,
        status: str = "active",
        full_name: Optional[str] = None,
        failed_attempts: int = 0,
        login_locked_until: Optional[datetime] = None,
        last_login_at: Optional[datetime] = None,
        token_current_jti: Optional[str] = None,
        otp_code: Optional[str] = None,
        otp_created_at: Optional[datetime] = None,
        otp_expires_at: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        # --------------------------------------------------------------
        # Identidad y credenciales
        # --------------------------------------------------------------
        self.id = id
        self.email = email
        self.full_name = full_name
        self.password_hash = password_hash

        # --------------------------------------------------------------
        # Rol (FK)
        # --------------------------------------------------------------
        self.role_id = role_id

        # --------------------------------------------------------------
        # Estado / seguridad / lockout
        # --------------------------------------------------------------
        self.status = status
        self.failed_attempts = failed_attempts
        self.login_locked_until = login_locked_until
        self.last_login_at = last_login_at

        # --------------------------------------------------------------
        # JWT (JTI actual) y OTP
        # --------------------------------------------------------------
        self.token_current_jti = token_current_jti
        self.otp_code = otp_code
        self.otp_created_at = otp_created_at
        self.otp_expires_at = otp_expires_at

        # --------------------------------------------------------------
        # Auditoría
        # --------------------------------------------------------------
        self.created_at = created_at
        self.updated_at = updated_at

    # ------------------------------------------------------------------
    # Reglas de negocio: estado
    # ------------------------------------------------------------------

    def is_active(self) -> bool:
        """Indica si el usuario está activo."""
        return self.status == "active"

    def is_blocked(self) -> bool:
        """Indica si el usuario está bloqueado."""
        return self.status == "blocked"

    # ------------------------------------------------------------------
    # Reglas de negocio: lockout por intentos fallidos
    # ------------------------------------------------------------------

    def is_login_locked(self, now: Optional[datetime] = None) -> bool:
        """
        Regla:
        - Si login_locked_until existe y está en el futuro -> locked.
        """
        if self.login_locked_until is None:
            return False

        now = now or utc_now()

        locked_until = ensure_aware_utc(self.login_locked_until)
        if locked_until is None:
            return False

        return locked_until > now

    def lock_login_for(self, minutes: int, now: Optional[datetime] = None) -> None:
        """
        Bloquea el login por X minutos.

        Nota:
        - El lock es una marca temporal; no cambia el status del usuario.
        """
        now = now or datetime.now(timezone.utc)
        self.login_locked_until = now + timedelta(minutes=minutes)

    def register_failed_attempt(
        self,
        *,
        max_attempts: int = 3,
        lock_minutes: int = 60,
        now: Optional[datetime] = None,
    ) -> None:
        """
        Registra un intento fallido de autenticación.

        Regla:
        - Incrementa failed_attempts
        - Si llega a max_attempts -> lock por lock_minutes
        """
        now = now or datetime.now(timezone.utc)

        # Incremento defensivo (DB también tiene CHECK >= 0)
        self.failed_attempts = max(0, int(self.failed_attempts)) + 1

        # Si alcanza el umbral, bloqueamos y reiniciamos contador
        # (Decisión tuya: yo recomiendo resetear para que el lock sea el control real)
        if self.failed_attempts >= max_attempts:
            self.lock_login_for(lock_minutes, now=now)
            self.failed_attempts = 0

    def reset_failed_attempts(self) -> None:
        """
        Reinicia la seguridad de intentos fallidos.

        Cuándo usar:
        - Login exitoso por password u OTP.
        """
        self.failed_attempts = 0
        self.login_locked_until = None

    # ------------------------------------------------------------------
    # Reglas de negocio: permisos de login
    # ------------------------------------------------------------------

    def can_login(self, now: Optional[datetime] = None) -> bool:
        """
        Regla de negocio:
        - Debe estar activo
        - No debe estar bloqueado por lockout temporal
        """
        if not self.is_active():
            return False

        if self.is_login_locked(now=now):
            return False

        return True