# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/infrastructure/fee_transaction_model.py
#
# Modelo ORM para la tabla fee_transactions.
# ======================================================================

from __future__ import annotations

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.mysql import TIMESTAMP

from app.extensions.db.base import Base, MYSQL_TABLE_OPTIONS


class FeeTransactionModel(Base):
    __tablename__ = "fee_transactions"
    __table_args__ = (
        # Un período → máximo una fee_transaction
        UniqueConstraint("billing_period_id", name="uq_fee_transactions_period"),
        Index("idx_fee_transactions_managed_account", "managed_account_id"),
        Index("idx_fee_transactions_status", "status"),
        CheckConstraint(
            "`status` IN ('pending', 'charged', 'waived')",
            name="chk_fee_transactions_status",
        ),
        CheckConstraint("`amount` >= 0", name="chk_fee_transactions_amount"),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    billing_period_id = Column(
        BigInteger,
        ForeignKey("billing_periods.id", name="fk_fee_transactions_billing_period"),
        nullable=False,
    )
    managed_account_id = Column(
        BigInteger,
        ForeignKey("managed_accounts.id", name="fk_fee_transactions_managed_account"),
        nullable=False,
    )
    amount = Column(
        Numeric(30, 12),
        nullable=False,
        default="0.000000000000",
        server_default=text("'0.000000000000'"),
    )
    status = Column(String(16), nullable=False, default="pending", server_default=text("'pending'"))
    charged_at = Column(TIMESTAMP(fsp=6), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
