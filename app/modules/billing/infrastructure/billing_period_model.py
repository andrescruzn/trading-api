# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/infrastructure/billing_period_model.py
#
# Modelo ORM para la tabla billing_periods.
# ======================================================================

from __future__ import annotations

from sqlalchemy import BigInteger, Column, Numeric, String, TIMESTAMP
from sqlalchemy.sql import func

from app.extensions.db.base import Base


class BillingPeriodModel(Base):
    __tablename__ = "billing_periods"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    managed_account_id = Column(BigInteger, nullable=False)
    start_ts = Column(
        TIMESTAMP(timezone=False),
        nullable=False,
        server_default=func.now(),
    )
    end_ts = Column(TIMESTAMP(timezone=False), nullable=True)
    opening_equity = Column(Numeric(30, 12), nullable=False, default="0.000000000000")
    closing_equity = Column(Numeric(30, 12), nullable=True)
    gross_pnl = Column(Numeric(30, 12), nullable=True)
    fee_pct = Column(Numeric(5, 4), nullable=False, default="0.0000")
    fee_amount = Column(Numeric(30, 12), nullable=True)
    net_pnl = Column(Numeric(30, 12), nullable=True)
    status = Column(String(16), nullable=False, default="open")
    created_at = Column(
        TIMESTAMP(timezone=False),
        nullable=False,
        server_default=func.now(),
    )
    closed_at = Column(TIMESTAMP(timezone=False), nullable=True)
