# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/infrastructure/signal_model.py
#
# Modelo SQLAlchemy para la tabla `signals`.
# Incluye las columnas de precio agregadas en la migración M07.
# ======================================================================

from sqlalchemy import BigInteger, Column, DECIMAL, ForeignKey, JSON, String, TIMESTAMP, text
from sqlalchemy.dialects.mysql import TINYINT

from app.extensions.db import Base


class SignalModel(Base):
    """Modelo SQLAlchemy para la tabla `signals`."""

    __tablename__ = "signals"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    bot_id = Column(
        BigInteger,
        ForeignKey("bots.id"),
        nullable=False,
        index=True,
    )
    ts = Column(TIMESTAMP(6), nullable=False)
    action = Column(String(8), nullable=False)

    # Columnas de precio (M07) — nullable porque hold no tiene precios
    entry_price   = Column(DECIMAL(30, 12), nullable=True)
    stop_loss     = Column(DECIMAL(30, 12), nullable=True)
    take_profit   = Column(DECIMAL(30, 12), nullable=True)
    position_size = Column(DECIMAL(30, 12), nullable=True)
    rr_ratio      = Column(DECIMAL(10, 4),  nullable=True)

    # 1 = aprobada, 0 = rechazada por algún filtro (régimen, reglas o R/R)
    approved = Column(TINYINT(1), nullable=False, server_default=text("'1'"))

    confidence    = Column(DECIMAL(6, 5), nullable=True)
    model_version = Column(String(64), nullable=True)
    features_hash = Column(String(128), nullable=True)
    reasons       = Column(JSON, nullable=False)
    created_at    = Column(
        TIMESTAMP(6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
