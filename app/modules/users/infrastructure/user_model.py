# app/modules/users/infrastructure/user_model.py
# -*- coding: utf-8 -*-

# ======================================================================
# SQLAlchemy User Model
# ----------------------------------------------------------------------
# Modelo de persistencia que representa la tabla `users`.
#
# CAMBIOS CLAVE:
# - role_id (FK a roles.id)
# - login_locked_until (TIMESTAMP(6) NULL) para lockout de 1h tras 3 fallos
# ======================================================================

from sqlalchemy import (
    BigInteger,
    Column,
    ForeignKey,
    Integer,
    String,
    TIMESTAMP,
    text,
)
from app.extensions.db import Base


class UserModel(Base):
    """
    Modelo SQLAlchemy para la tabla `users`.
    """

    __tablename__ = "users"

    # ------------------------------------------------------------------
    # PK
    # ------------------------------------------------------------------
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # ------------------------------------------------------------------
    # Identidad
    # ------------------------------------------------------------------
    email = Column(String(255), nullable=False, unique=True)
    full_name = Column(String(255), nullable=True)

    # ------------------------------------------------------------------
    # Credenciales
    # ------------------------------------------------------------------
    password_hash = Column(String(255), nullable=False)

    # --------------------------------------------------------------
    # Rol (FK)
    # --------------------------------------------------------------
    role_id = Column(
        BigInteger,
        ForeignKey("roles.id"),  # requiere RoleModel cargado en metadata
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------------
    # Estado / seguridad
    # ------------------------------------------------------------------
    status = Column(String(16), nullable=False, server_default=text("'active'"))

    # Intentos fallidos acumulados (en verificación real: password/otp)
    failed_attempts = Column(Integer, nullable=False, server_default=text("0"))

    # Bloqueo temporal por seguridad (ej: 1h tras 3 fallos)
    login_locked_until = Column(TIMESTAMP(6), nullable=True, index=True)

    # Auditoría de acceso
    last_login_at = Column(TIMESTAMP(6), nullable=True)

    # JTI actual para invalidación/rotación de sesiones
    token_current_jti = Column(String(64), nullable=True)

    # ------------------------------------------------------------------
    # OTP
    # ------------------------------------------------------------------
    otp_code = Column(String(255), nullable=True)
    otp_created_at = Column(TIMESTAMP(6), nullable=True)
    otp_expires_at = Column(TIMESTAMP(6), nullable=True)

    # ------------------------------------------------------------------
    # Auditoría
    # ------------------------------------------------------------------
    created_at = Column(
        TIMESTAMP(6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
    updated_at = Column(
        TIMESTAMP(6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
        onupdate=text("CURRENT_TIMESTAMP(6)"),
    )