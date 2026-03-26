# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/infrastructure/managed_account_model.py
#
# Modelo ORM para la tabla managed_accounts.
# ======================================================================

from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, Column, Numeric, String, TIMESTAMP
from sqlalchemy.sql import func

from app.extensions.db.base import Base


class ManagedAccountModel(Base):
    __tablename__ = "managed_accounts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    investor_id = Column(BigInteger, nullable=False)
    account_id = Column(BigInteger, nullable=False)
    bot_id = Column(BigInteger, nullable=True)
    name = Column(String(120), nullable=False)
    initial_capital = Column(Numeric(30, 12), nullable=False, default="0.000000000000")
    high_water_mark = Column(Numeric(30, 12), nullable=False, default="0.000000000000")
    period_type = Column(String(16), nullable=False, default="monthly")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        TIMESTAMP(timezone=False),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        TIMESTAMP(timezone=False),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
