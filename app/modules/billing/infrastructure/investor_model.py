# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/infrastructure/investor_model.py
#
# Modelo ORM para la tabla investors.
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
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.mysql import TIMESTAMP
from sqlalchemy.sql import func

from app.extensions.db.base import Base, MYSQL_TABLE_OPTIONS


class InvestorModel(Base):
    __tablename__ = "investors"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_investors_user_id"),
        Index("idx_investors_active", "is_active"),
        CheckConstraint("`fee_pct` >= 0 AND `fee_pct` <= 1", name="chk_investors_fee_pct"),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(
        BigInteger,
        ForeignKey("users.id", name="fk_investors_user", ondelete="CASCADE"),
        nullable=False,
    )
    fee_pct = Column(
        Numeric(5, 4),
        nullable=False,
        default="0.2000",
        server_default=text("'0.2000'"),
        comment="Performance fee ej: 0.2000 = 20%",
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
