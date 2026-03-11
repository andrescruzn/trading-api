# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/features/infrastructure/candle_feature_model.py
#
# Modelo SQLAlchemy para la tabla `candle_features`.
# ======================================================================

from sqlalchemy import BigInteger, Column, ForeignKey, JSON, SmallInteger, TIMESTAMP, text

from app.extensions.db import Base


class CandleFeatureModel(Base):
    """Modelo SQLAlchemy para la tabla `candle_features`."""

    __tablename__ = "candle_features"

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
    feature_set_id = Column(
        BigInteger,
        ForeignKey("feature_sets.id"),
        nullable=False,
        index=True,
    )
    features = Column(JSON, nullable=False)
    created_at = Column(
        TIMESTAMP(6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
