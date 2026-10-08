# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/infrastructure/managed_account_model.py
#
# Modelo ORM para la tabla managed_accounts.
# ======================================================================

from __future__ import annotations

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Numeric,
    String,
    text,
)
from sqlalchemy.dialects.mysql import TIMESTAMP
from sqlalchemy.sql import func

from app.extensions.db.base import Base, MYSQL_TABLE_OPTIONS


class ManagedAccountModel(Base):
    __tablename__ = "managed_accounts"
    __table_args__ = (
        Index("idx_managed_accounts_investor", "investor_id"),
        Index("idx_managed_accounts_account", "account_id"),
        Index("idx_managed_accounts_bot", "bot_id"),
        Index("idx_managed_accounts_active", "is_active"),
        CheckConstraint(
            "`period_type` IN ('daily', 'weekly', 'monthly')",
            name="chk_managed_accounts_period_type",
        ),
        CheckConstraint(
            "`initial_capital` >= 0 AND `high_water_mark` >= 0",
            name="chk_managed_accounts_capital",
        ),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    investor_id = Column(
        BigInteger,
        ForeignKey("investors.id", name="fk_managed_accounts_investor"),
        nullable=False,
    )
    account_id = Column(
        BigInteger,
        ForeignKey("accounts.id", name="fk_managed_accounts_account"),
        nullable=False,
    )
    bot_id = Column(
        BigInteger,
        ForeignKey("bots.id", name="fk_managed_accounts_bot"),
        nullable=True,
    )
    name = Column(String(120), nullable=False)
    initial_capital = Column(
        Numeric(30, 12),
        nullable=False,
        default="0.000000000000",
        server_default=text("'0.000000000000'"),
        comment="Capital inicial aportado por el inversor",
    )
    high_water_mark = Column(
        Numeric(30, 12),
        nullable=False,
        default="0.000000000000",
        server_default=text("'0.000000000000'"),
        comment="Máximo equity histórico alcanzado (base para HWM fee)",
    )
    period_type = Column(
        String(16),
        nullable=False,
        default="monthly",
        server_default=text("'monthly'"),
        comment="Frecuencia de facturación: daily | weekly | monthly",
    )
    is_active = Column(Boolean, nullable=False, default=True, server_default=text("1"))
    created_at = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
    updated_at = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)"),
        onupdate=func.now(),
    )
