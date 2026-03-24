# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/infrastructure/position_model.py
#
# Modelo SQLAlchemy para la tabla `positions`.
# Representa la posición abierta actual de un bot en un símbolo.
# Tiene una restricción UNIQUE (bot_id, symbol_id) — un bot solo
# puede tener una posición activa por símbolo a la vez.
# ======================================================================

from sqlalchemy import BigInteger, Column, ForeignKey, NUMERIC, TIMESTAMP, text

from app.extensions.db import Base


class PositionModel(Base):
    """Modelo SQLAlchemy para la tabla `positions`."""

    __tablename__ = "positions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    bot_id = Column(
        BigInteger,
        ForeignKey("bots.id"),
        nullable=False,
        index=True,
    )
    symbol_id = Column(
        BigInteger,
        ForeignKey("symbols.id"),
        nullable=False,
    )

    # Estado de la posición
    qty = Column(
        NUMERIC(30, 12),
        nullable=False,
        server_default=text("'0.000000000000'"),
    )
    avg_price = Column(
        NUMERIC(30, 12),
        nullable=False,
        server_default=text("'0.000000000000'"),
    )
    realized_pnl = Column(
        NUMERIC(30, 12),
        nullable=False,
        server_default=text("'0.000000000000'"),
    )

    updated_at = Column(
        TIMESTAMP(6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)"),
    )
