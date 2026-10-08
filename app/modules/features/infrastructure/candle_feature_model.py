# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/features/infrastructure/candle_feature_model.py
#
# Modelo SQLAlchemy para la tabla `candle_features`.
#
# NOTA: los índices de `timeframe_id` y `feature_set_id` los crea MySQL solo,
# con el nombre de su FK: no se declaran.
# ======================================================================

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    JSON,
    SmallInteger,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.mysql import TIMESTAMP

from app.extensions.db import Base, MYSQL_TABLE_OPTIONS


class CandleFeatureModel(Base):
    """Modelo SQLAlchemy para la tabla `candle_features`."""

    __tablename__ = "candle_features"
    __table_args__ = (
        UniqueConstraint(
            "symbol_id", "timeframe_id", "ts", "feature_set_id",
            name="uq_candle_features",
        ),
        Index(
            "idx_candle_features_lookup",
            "symbol_id", "timeframe_id", "ts", "feature_set_id",
        ),
        CheckConstraint("json_valid(`features`)", name="chk_candle_features_json"),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    symbol_id = Column(
        BigInteger,
        ForeignKey("symbols.id", name="fk_candle_features_symbol"),
        nullable=False,
    )
    timeframe_id = Column(
        SmallInteger,
        ForeignKey("timeframes.id", name="fk_candle_features_timeframe"),
        nullable=False,
    )
    ts = Column(TIMESTAMP(fsp=6), nullable=False)
    feature_set_id = Column(
        BigInteger,
        ForeignKey("feature_sets.id", name="fk_candle_features_set"),
        nullable=False,
    )
    features = Column(JSON, nullable=False)
    created_at = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
