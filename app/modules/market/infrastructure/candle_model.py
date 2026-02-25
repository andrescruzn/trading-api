# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/market/infrastructure/candle_model.py
#
# Modelo SQLAlchemy para la tabla `candles` (OHLCV).
# ======================================================================

from sqlalchemy import BigInteger, Column, ForeignKey, NUMERIC, SmallInteger, TIMESTAMP, text

from app.extensions.db import Base


class CandleModel(Base):
    """Modelo SQLAlchemy para la tabla `candles`."""

    __tablename__ = "candles"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    symbol_id = Column(
        BigInteger,
        ForeignKey("symbols.id"),
        nullable=False,
        index=True,
    )
    timeframe_id = Column(
        SmallInteger,
        ForeignKey("timeframes.id"),
        nullable=False,
        index=True,
    )
    ts = Column(TIMESTAMP(6), nullable=False)

    # DECIMAL(30,12) para precisión financiera
    open = Column(NUMERIC(30, 12), nullable=False)
    high = Column(NUMERIC(30, 12), nullable=False)
    low = Column(NUMERIC(30, 12), nullable=False)
    close = Column(NUMERIC(30, 12), nullable=False)
    volume = Column(NUMERIC(30, 12), nullable=False, server_default=text("0"))

    created_at = Column(
        TIMESTAMP(6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
