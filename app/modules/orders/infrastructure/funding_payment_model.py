# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/infrastructure/funding_payment_model.py
#
# Modelo SQLAlchemy para la tabla `funding_payments`: lo que Binance cobra o
# paga de funding sobre la posición de un perpetuo en live.
# ======================================================================

from sqlalchemy import (
    DECIMAL,
    BigInteger,
    Column,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.mysql import TIMESTAMP

from app.extensions.db import Base, MYSQL_TABLE_OPTIONS


class FundingPaymentModel(Base):
    """Funding de un perpetuo: positivo = la cuenta recibió, negativo = pagó."""

    __tablename__ = "funding_payments"
    __table_args__ = (
        UniqueConstraint(
            "account_id", "exchange_funding_id", name="uq_funding_payments_account_exchange_id"
        ),
        Index("idx_funding_payments_bot_ts", "bot_id", "ts"),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    bot_id = Column(
        BigInteger,
        ForeignKey("bots.id", name="fk_funding_payments_bot"),
        nullable=False,
    )
    account_id = Column(
        BigInteger,
        ForeignKey("accounts.id", name="fk_funding_payments_account"),
        nullable=False,
    )
    symbol_id = Column(
        BigInteger,
        ForeignKey("symbols.id", name="fk_funding_payments_symbol"),
        nullable=False,
    )
    amount = Column(DECIMAL(30, 12), nullable=False, comment="Con signo: + recibido, − pagado")
    asset = Column(String(32), nullable=False, comment="Moneda del funding (USDT)")
    exchange_funding_id = Column(String(64), nullable=False, comment="Id del registro en Binance")
    ts = Column(TIMESTAMP(fsp=6), nullable=False, comment="Cuándo lo liquidó el exchange")
    created_at = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
