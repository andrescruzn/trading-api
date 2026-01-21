# app/modules/users/domain/user_entity.py
# -*- coding: utf-8 -*-

# ======================================================================
# User Domain Entity
# ----------------------------------------------------------------------
# Representa un usuario del sistema desde el punto de vista del dominio.
# No depende de framework, ORM ni infraestructura.
# ======================================================================

from datetime import datetime
from typing import Optional


class User:
    """
    Entidad de dominio: User

    Responsabilidad:
    - Modelar el concepto de usuario
    - Encapsular reglas básicas de negocio
    """

    def __init__(
        self,
        id: int,
        email: str,
        password_hash: str,
        role: str = "user",
        status: str = "active",
        full_name: Optional[str] = None,
        failed_attempts: int = 0,
        last_login_at: Optional[datetime] = None,
        token_current_jti: Optional[str] = None,
        otp_code: Optional[str] = None,
        otp_created_at: Optional[datetime] = None,
        otp_expires_at: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id
        self.email = email
        self.full_name = full_name
        self.password_hash = password_hash
        self.role = role
        self.status = status
        self.failed_attempts = failed_attempts
        self.last_login_at = last_login_at
        self.token_current_jti = token_current_jti
        self.otp_code = otp_code
        self.otp_created_at = otp_created_at
        self.otp_expires_at = otp_expires_at
        self.created_at = created_at
        self.updated_at = updated_at

    # ------------------------------------------------------------------
    # Reglas de negocio
    # ------------------------------------------------------------------

    def is_active(self) -> bool:
        """Indica si el usuario está activo"""
        return self.status == "active"

    def is_blocked(self) -> bool:
        """Indica si el usuario está bloqueado"""
        return self.status == "blocked"

    def can_login(self) -> bool:
        """
        Regla de negocio:
        Un usuario solo puede autenticarse si está activo
        """
        return self.is_active()