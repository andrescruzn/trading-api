# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/agent/infrastructure/prediction_model.py
#
# Modelo SQLAlchemy para la tabla `predictions`.
#
# NOTAS:
# - Una predicción por (bot, modelo, símbolo, timeframe, vela). `raw_output`
#   guarda el snapshot del análisis (AnalysisResult.to_dict()).
# - Hoy ningún servicio escribe en esta tabla; el modelo existe para que el
#   esquema completo lo gestione Alembic.
# - El índice de `model_id` y el de `timeframe_id` los crea MySQL solo, con el
#   nombre de su FK: no se declaran.
# ======================================================================

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    DECIMAL,
    ForeignKey,
    Index,
    JSON,
    SmallInteger,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.mysql import TIMESTAMP

from app.extensions.db import Base, MYSQL_TABLE_OPTIONS


class PredictionModel(Base):
    """Modelo SQLAlchemy para la tabla `predictions`."""

    __tablename__ = "predictions"
    __table_args__ = (
        UniqueConstraint(
            "bot_id", "model_id", "symbol_id", "timeframe_id", "ts",
            name="uq_predictions",
        ),
        Index("idx_predictions_bot_ts", "bot_id", "ts"),
        Index("idx_predictions_symbol_tf_ts", "symbol_id", "timeframe_id", "ts"),
        CheckConstraint("json_valid(`raw_output`)", name="chk_predictions_raw_output_json"),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    bot_id = Column(
        BigInteger,
        ForeignKey("bots.id", name="fk_predictions_bot", ondelete="CASCADE"),
        nullable=False,
    )
    model_id = Column(
        BigInteger,
        ForeignKey("models.id", name="fk_predictions_model"),
        nullable=True,
    )
    symbol_id = Column(
        BigInteger,
        ForeignKey("symbols.id", name="fk_predictions_symbol"),
        nullable=False,
    )
    timeframe_id = Column(
        SmallInteger,
        ForeignKey("timeframes.id", name="fk_predictions_timeframe"),
        nullable=False,
    )
    ts = Column(TIMESTAMP(fsp=6), nullable=False)
    score = Column(DECIMAL(12, 8), nullable=True)
    raw_output = Column(JSON, nullable=False)
    created_at = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
