# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/infrastructure/signal_model.py
#
# Modelo SQLAlchemy para la tabla `signals`.
# Incluye las columnas de precio agregadas en la migración M07.
# ======================================================================

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    DECIMAL,
    ForeignKey,
    Index,
    JSON,
    String,
    text,
)
from sqlalchemy.dialects.mysql import TIMESTAMP, TINYINT

from app.extensions.db import Base, MYSQL_TABLE_OPTIONS


class SignalModel(Base):
    """Modelo SQLAlchemy para la tabla `signals`."""

    __tablename__ = "signals"
    __table_args__ = (
        Index("idx_signals_bot_ts", "bot_id", "ts"),
        CheckConstraint("`action` IN ('buy', 'sell', 'hold')", name="chk_signals_action"),
        CheckConstraint(
            "`confidence` IS NULL OR (`confidence` >= 0 AND `confidence` <= 1)",
            name="chk_signals_confidence",
        ),
        CheckConstraint("json_valid(`reasons`)", name="chk_signals_reasons_json"),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    bot_id = Column(
        BigInteger,
        ForeignKey("bots.id", name="fk_signals_bot"),
        nullable=False,
    )
    ts = Column(TIMESTAMP(fsp=6), nullable=False)
    action = Column(String(8), nullable=False)

    # Columnas de precio (M07) — nullable porque hold no tiene precios
    entry_price   = Column(DECIMAL(30, 12), nullable=True, comment="Precio de entrada sugerido por el agente")
    stop_loss     = Column(DECIMAL(30, 12), nullable=True, comment="Nivel de stop loss calculado")
    take_profit   = Column(DECIMAL(30, 12), nullable=True, comment="Nivel de take profit calculado")
    position_size = Column(
        DECIMAL(30, 12),
        nullable=True,
        comment="Tamaño de posición: capital × risk_pct / |entry-SL|",
    )
    rr_ratio      = Column(
        DECIMAL(10, 4),
        nullable=True,
        comment="Ratio Riesgo/Recompensa (TP-entry)/(entry-SL)",
    )

    # 1 = aprobada, 0 = rechazada por algún filtro (régimen, reglas o R/R)
    approved = Column(
        TINYINT(1),
        nullable=False,
        server_default=text("'1'"),
        comment="1=aprobada por todos los filtros, 0=rechazada",
    )

    confidence    = Column(DECIMAL(6, 5), nullable=True)
    model_version = Column(String(64), nullable=True)
    features_hash = Column(String(128), nullable=True)
    reasons       = Column(JSON, nullable=False)
    created_at    = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
