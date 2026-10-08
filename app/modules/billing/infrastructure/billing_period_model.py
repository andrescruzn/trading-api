# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/infrastructure/billing_period_model.py
#
# Modelo ORM para la tabla billing_periods.
# ======================================================================

from __future__ import annotations

from sqlalchemy import BigInteger, CheckConstraint, Column, ForeignKey, Index, Numeric, String, text
from sqlalchemy.dialects.mysql import TIMESTAMP

from app.extensions.db.base import Base, MYSQL_TABLE_OPTIONS


class BillingPeriodModel(Base):
    __tablename__ = "billing_periods"
    __table_args__ = (
        Index("idx_billing_periods_managed_account", "managed_account_id"),
        Index("idx_billing_periods_status", "status"),
        Index("idx_billing_periods_start_ts", "managed_account_id", "start_ts"),
        CheckConstraint("`status` IN ('open', 'closed')", name="chk_billing_periods_status"),
        CheckConstraint("`opening_equity` >= 0", name="chk_billing_periods_equity"),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    managed_account_id = Column(
        BigInteger,
        ForeignKey("managed_accounts.id", name="fk_billing_periods_managed_account"),
        nullable=False,
    )
    start_ts = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
    end_ts = Column(TIMESTAMP(fsp=6), nullable=True)
    opening_equity = Column(
        Numeric(30, 12),
        nullable=False,
        default="0.000000000000",
        server_default=text("'0.000000000000'"),
    )
    closing_equity = Column(Numeric(30, 12), nullable=True)
    gross_pnl = Column(
        Numeric(30, 12),
        nullable=True,
        comment="closing_equity - MAX(opening_equity, HWM)",
    )
    fee_pct = Column(
        Numeric(5, 4),
        nullable=False,
        default="0.0000",
        server_default=text("'0.0000'"),
        comment="Snapshot del fee_pct al abrir el período",
    )
    fee_amount = Column(Numeric(30, 12), nullable=True)
    net_pnl = Column(Numeric(30, 12), nullable=True, comment="gross_pnl - fee_amount")
    status = Column(String(16), nullable=False, default="open", server_default=text("'open'"))
    created_at = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
    closed_at = Column(TIMESTAMP(fsp=6), nullable=True)
