# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/infrastructure/fee_transaction_model.py
#
# Modelo ORM para la tabla fee_transactions.
# ======================================================================

from __future__ import annotations

from sqlalchemy import BigInteger, Column, Numeric, String, Text, TIMESTAMP
from sqlalchemy.sql import func

from app.extensions.db.base import Base


class FeeTransactionModel(Base):
    __tablename__ = "fee_transactions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    billing_period_id = Column(BigInteger, nullable=False, unique=True)
    managed_account_id = Column(BigInteger, nullable=False)
    amount = Column(Numeric(30, 12), nullable=False, default="0.000000000000")
    status = Column(String(16), nullable=False, default="pending")
    charged_at = Column(TIMESTAMP(timezone=False), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(
        TIMESTAMP(timezone=False),
        nullable=False,
        server_default=func.now(),
    )
