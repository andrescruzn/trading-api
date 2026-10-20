# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/infrastructure/capital_movement_model.py
#
# Modelo ORM para la tabla `capital_movements`: aportes (deposit) y
# retiros (withdrawal) del inversor en una cuenta gestionada. Ajustan la
# marca de agua para no cobrar comisión sobre dinero depositado.
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
    text,
)
from sqlalchemy.dialects.mysql import TIMESTAMP

from app.extensions.db.base import Base, MYSQL_TABLE_OPTIONS


class CapitalMovementModel(Base):
    __tablename__ = "capital_movements"
    __table_args__ = (
        Index("idx_capital_movements_account_ts", "managed_account_id", "ts"),
        CheckConstraint(
            "`kind` IN ('deposit', 'withdrawal')",
            name="chk_capital_movements_kind",
        ),
        CheckConstraint("`amount` > 0", name="chk_capital_movements_amount"),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    managed_account_id = Column(
        BigInteger,
        ForeignKey("managed_accounts.id", name="fk_capital_movements_managed_account"),
        nullable=False,
    )
    kind = Column(String(16), nullable=False, comment="deposit | withdrawal")
    amount = Column(Numeric(30, 12), nullable=False)
    ts = Column(TIMESTAMP(fsp=6), nullable=False, comment="Cuándo entró o salió el dinero")
    notes = Column(String(500), nullable=True)
    created_by_user_id = Column(
        BigInteger,
        ForeignKey("users.id", name="fk_capital_movements_created_by", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
