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
# - Sin lockout por intentos fallidos: la fuerza bruta se frena con
#   rate limit por correo e IP + expiración del OTP (ver routes de auth).
#
# NOTA:
# - El dominio define reglas puras (sin DB, sin HTTP, sin UI).
# - El cálculo de "ahora" lo recibe como argumento para testear fácil.
# ======================================================================

from __future__ import annotations

from datetime import datetime
from typing import Optional

class User:
    """
    Entidad de dominio: User

    Responsabilidad:
    - Modelar el usuario y su estado de autenticación
    - Encapsular reglas base de acceso (activo, bloqueado)
    """

    def __init__(
        self,
        id: int,
        email: str,
        role_id: int,
        status: str = "active",
        full_name: Optional[str] = None,
        last_login_at: Optional[datetime] = None,
        token_current_jti: Optional[str] = None,
        otp_code: Optional[str] = None,
        otp_created_at: Optional[datetime] = None,
        otp_expires_at: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        # --------------------------------------------------------------
        # Identidad
        # --------------------------------------------------------------
        self.id = id
        self.email = email
        self.full_name = full_name

        # --------------------------------------------------------------
        # Rol (FK)
        # --------------------------------------------------------------
        self.role_id = role_id

        # --------------------------------------------------------------
        # Estado / acceso
        # --------------------------------------------------------------
        self.status = status
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
