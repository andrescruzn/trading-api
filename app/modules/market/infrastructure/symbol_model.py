# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/market/infrastructure/symbol_model.py
#
# Modelo SQLAlchemy para la tabla `symbols`.
# ======================================================================

from sqlalchemy import BigInteger, Boolean, Column, ForeignKey, NUMERIC, String, TIMESTAMP, text

from app.extensions.db import Base


class SymbolModel(Base):
    """Modelo SQLAlchemy para la tabla `symbols`."""

    __tablename__ = "symbols"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    exchange_id = Column(
        BigInteger,
        ForeignKey("exchanges.id"),
        nullable=False,
        index=True,
    )
    symbol = Column(String(64), nullable=False)
    base_asset = Column(String(32), nullable=True)
    quote_asset = Column(String(32), nullable=True)
    asset_class = Column(String(16), nullable=False)

    # DECIMAL(30,12) para precisión financiera
    tick_size = Column(NUMERIC(30, 12), nullable=True)
    lot_size = Column(NUMERIC(30, 12), nullable=True)

    is_active = Column(Boolean, nullable=False, server_default=text("1"))
    created_at = Column(
        TIMESTAMP(6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
