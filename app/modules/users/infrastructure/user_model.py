# app/modules/users/infrastructure/user_model.py
# -*- coding: utf-8 -*-

# ======================================================================
# SQLAlchemy User Model
# ----------------------------------------------------------------------
# Modelo de persistencia que representa la tabla `users`
# ======================================================================

from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Integer,
    TIMESTAMP,
    text,
)
from app.extensions.db import Base


class UserModel(Base):
    """
    Modelo SQLAlchemy para la tabla `users`
    """

    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    email = Column(String(255), nullable=False, unique=True)
    full_name = Column(String(255), nullable=True)
    password_hash = Column(String(255), nullable=False)

    role = Column(String(16), nullable=False, server_default=text("'user'"))
    status = Column(String(16), nullable=False, server_default=text("'active'"))

    failed_attempts = Column(Integer, nullable=False, server_default=text("0"))
    last_login_at = Column(TIMESTAMP(6), nullable=True)

    token_current_jti = Column(String(64), nullable=True)

    otp_code = Column(String(255), nullable=True)
    otp_created_at = Column(TIMESTAMP(6), nullable=True)
    otp_expires_at = Column(TIMESTAMP(6), nullable=True)

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