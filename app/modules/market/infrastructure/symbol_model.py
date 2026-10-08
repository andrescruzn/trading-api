# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/market/infrastructure/symbol_model.py
#
# Modelo SQLAlchemy para la tabla `symbols`.
# ======================================================================

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    NUMERIC,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.mysql import TIMESTAMP

from app.extensions.db import Base, MYSQL_TABLE_OPTIONS


class SymbolModel(Base):
    """Modelo SQLAlchemy para la tabla `symbols`."""

    __tablename__ = "symbols"
    __table_args__ = (
        UniqueConstraint("exchange_id", "symbol", name="uq_symbols_exchange_symbol"),
        Index("idx_symbols_exchange", "exchange_id"),
        Index("idx_symbols_asset_class", "asset_class"),
        CheckConstraint(
            "`asset_class` IN ('crypto', 'metal', 'etf', 'stock', 'forex')",
            name="chk_symbols_asset_class",
        ),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    exchange_id = Column(
        BigInteger,
        ForeignKey("exchanges.id", name="fk_symbols_exchange"),
        nullable=False,
    )
    symbol = Column(String(64), nullable=False)
    base_asset = Column(String(32), nullable=True)
    quote_asset = Column(String(32), nullable=True)
    asset_class = Column(String(16), nullable=False)

    # DECIMAL(30,12) para precisión financiera
    tick_size = Column(NUMERIC(30, 12), nullable=True)
    lot_size = Column(NUMERIC(30, 12), nullable=True)

    is_active = Column(Boolean, nullable=False, server_default=text("'1'"))
    created_at = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
