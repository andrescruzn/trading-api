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
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.mysql import TIMESTAMP

from app.extensions.db import Base, MYSQL_TABLE_OPTIONS


class UserModel(Base):
    """
    Modelo SQLAlchemy para la tabla `users`.
    """

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        Index("idx_users_status", "status"),
        Index("idx_users_token_jti", "token_current_jti"),
        Index("idx_users_otp_expires", "otp_expires_at"),
        Index("idx_users_role_id", "role_id"),
        Index("idx_users_login_locked_until", "login_locked_until"),
        CheckConstraint("`failed_attempts` >= 0", name="chk_users_failed_attempts"),
        CheckConstraint(
            "`otp_created_at` IS NULL OR `otp_expires_at` IS NULL "
            "OR `otp_expires_at` >= `otp_created_at`",
            name="chk_users_otp_dates",
        ),
        CheckConstraint(
            "`status` IN ('active', 'blocked', 'disabled')",
            name="chk_users_status",
        ),
        MYSQL_TABLE_OPTIONS,
    )

    # ------------------------------------------------------------------
    # PK
    # ------------------------------------------------------------------
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # ------------------------------------------------------------------
    # Identidad
    # ------------------------------------------------------------------
    email = Column(String(255), nullable=False)
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
        ForeignKey("roles.id", name="fk_users_role"),  # requiere RoleModel cargado en metadata
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Estado / seguridad
    # ------------------------------------------------------------------
    status = Column(String(16), nullable=False, server_default=text("'active'"))

    # Intentos fallidos acumulados (en verificación real: password/otp)
    failed_attempts = Column(Integer, nullable=False, server_default=text("'0'"))

    # Bloqueo temporal por seguridad (ej: 1h tras 3 fallos)
    login_locked_until = Column(TIMESTAMP(fsp=6), nullable=True)

    # Auditoría de acceso
    last_login_at = Column(TIMESTAMP(fsp=6), nullable=True)

    # JTI actual para invalidación/rotación de sesiones
    token_current_jti = Column(String(64), nullable=True)

    # ------------------------------------------------------------------
    # OTP
    # ------------------------------------------------------------------
    otp_code = Column(String(255), nullable=True)
    otp_created_at = Column(TIMESTAMP(fsp=6), nullable=True)
    otp_expires_at = Column(TIMESTAMP(fsp=6), nullable=True)

    # ------------------------------------------------------------------
    # Auditoría
    # ------------------------------------------------------------------
    created_at = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
    updated_at = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)"),
        onupdate=text("CURRENT_TIMESTAMP(6)"),
    )
