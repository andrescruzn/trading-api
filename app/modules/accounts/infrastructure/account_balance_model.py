# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/accounts/infrastructure/account_balance_model.py
#
# Modelo SQLAlchemy para la tabla `account_balances`.
# ======================================================================

from sqlalchemy import BigInteger, Column, DECIMAL, ForeignKey, String, TIMESTAMP, text

from app.extensions.db import Base


class AccountBalanceModel(Base):
    """Modelo SQLAlchemy para la tabla `account_balances`."""

    __tablename__ = "account_balances"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    account_id = Column(
        BigInteger,
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    asset = Column(String(32), nullable=False)
    free = Column(DECIMAL(30, 12), nullable=False, server_default=text("'0.000000000000'"))
    locked = Column(DECIMAL(30, 12), nullable=False, server_default=text("'0.000000000000'"))
    ts = Column(
        TIMESTAMP(6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
