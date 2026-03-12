# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/accounts/infrastructure/account_model.py
#
# Modelo SQLAlchemy para la tabla `accounts`.
# ======================================================================

from sqlalchemy import BigInteger, Column, ForeignKey, JSON, String, TIMESTAMP, text

from app.extensions.db import Base


class AccountModel(Base):
    """Modelo SQLAlchemy para la tabla `accounts`."""

    __tablename__ = "accounts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    exchange_id = Column(
        BigInteger,
        ForeignKey("exchanges.id"),
        nullable=True,
        index=True,
    )
    name = Column(String(120), nullable=False)
    mode = Column(String(8), nullable=False)
    base_currency = Column(String(16), nullable=False, server_default=text("'USD'"))
    status = Column(String(16), nullable=False, server_default=text("'active'"))
    credentials_ref = Column(String(255), nullable=True)
    meta = Column(JSON, nullable=False)
    created_at = Column(
        TIMESTAMP(6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
    updated_at = Column(
        TIMESTAMP(6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)"),
    )
