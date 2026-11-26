# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/accounts/infrastructure/account_balance_model.py
#
# Modelo SQLAlchemy para la tabla `account_balances`.
# ======================================================================

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    DECIMAL,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.mysql import TIMESTAMP

from app.extensions.db import Base, MYSQL_TABLE_OPTIONS


class AccountBalanceModel(Base):
    """Modelo SQLAlchemy para la tabla `account_balances`."""

    __tablename__ = "account_balances"
    __table_args__ = (
        UniqueConstraint("account_id", "asset", "ts", name="uq_balances_account_asset_ts"),
        Index("idx_balances_account_ts", "account_id", "ts"),
        CheckConstraint("`free` >= 0 AND `locked` >= 0", name="chk_balances_amounts"),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    account_id = Column(
        BigInteger,
        ForeignKey("accounts.id", name="fk_balances_account", ondelete="CASCADE"),
        nullable=False,
    )
    asset = Column(String(32), nullable=False)
    free = Column(DECIMAL(30, 12), nullable=False, server_default=text("'0.000000000000'"))
    locked = Column(DECIMAL(30, 12), nullable=False, server_default=text("'0.000000000000'"))
    ts = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
