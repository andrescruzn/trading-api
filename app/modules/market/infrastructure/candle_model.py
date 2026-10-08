# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/market/infrastructure/candle_model.py
#
# Modelo SQLAlchemy para la tabla `candles` (OHLCV).
#
# NOTA: el índice de `timeframe_id` lo crea MySQL solo, con el nombre de su
# FK (`fk_candles_timeframe`): no se declara.
# ======================================================================

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    NUMERIC,
    SmallInteger,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.mysql import TIMESTAMP

from app.extensions.db import Base, MYSQL_TABLE_OPTIONS


class CandleModel(Base):
    """Modelo SQLAlchemy para la tabla `candles`."""

    __tablename__ = "candles"
    __table_args__ = (
        UniqueConstraint("symbol_id", "timeframe_id", "ts", name="uq_candles_symbol_tf_ts"),
        Index("idx_candles_symbol_tf_ts", "symbol_id", "timeframe_id", "ts"),
        CheckConstraint("`high` >= `low`", name="chk_candles_high_low"),
        CheckConstraint(
            "`open` >= 0 AND `high` >= 0 AND `low` >= 0 AND `close` >= 0 AND `volume` >= 0",
            name="chk_candles_prices",
        ),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    symbol_id = Column(
        BigInteger,
        ForeignKey("symbols.id", name="fk_candles_symbol"),
        nullable=False,
    )
    timeframe_id = Column(
        SmallInteger,
        ForeignKey("timeframes.id", name="fk_candles_timeframe"),
        nullable=False,
    )
    ts = Column(TIMESTAMP(fsp=6), nullable=False)

    # DECIMAL(30,12) para precisión financiera
    open = Column(NUMERIC(30, 12), nullable=False)
    high = Column(NUMERIC(30, 12), nullable=False)
    low = Column(NUMERIC(30, 12), nullable=False)
    close = Column(NUMERIC(30, 12), nullable=False)
    volume = Column(NUMERIC(30, 12), nullable=False, server_default=text("'0.000000000000'"))

    created_at = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
