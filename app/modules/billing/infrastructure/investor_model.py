# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/infrastructure/investor_model.py
#
# Modelo ORM para la tabla investors.
# ======================================================================

from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, Column, Numeric, TIMESTAMP
from sqlalchemy.sql import func

from app.extensions.db.base import Base


class InvestorModel(Base):
    __tablename__ = "investors"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, unique=True)
    fee_pct = Column(Numeric(5, 4), nullable=False, default="0.2000")
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
