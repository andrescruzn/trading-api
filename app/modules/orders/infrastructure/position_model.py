# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/infrastructure/position_model.py
#
# Modelo SQLAlchemy para la tabla `positions`.
# Representa la posición abierta actual de un bot en un símbolo.
# Tiene una restricción UNIQUE (bot_id, symbol_id) — un bot solo
# puede tener una posición activa por símbolo a la vez.
#
# NOTA: el índice de `symbol_id` lo crea MySQL solo, con el nombre de su
# FK (`fk_positions_symbol`): no se declara.
# ======================================================================

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    NUMERIC,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.mysql import TIMESTAMP

from app.extensions.db import Base, MYSQL_TABLE_OPTIONS


class PositionModel(Base):
    """Modelo SQLAlchemy para la tabla `positions`."""

    __tablename__ = "positions"
    __table_args__ = (
        UniqueConstraint("bot_id", "symbol_id", name="uq_positions_bot_symbol"),
        Index("idx_positions_bot", "bot_id"),
        CheckConstraint("`avg_price` >= 0", name="chk_positions_prices"),
        CheckConstraint("`qty` >= 0", name="chk_positions_qty"),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    bot_id = Column(
        BigInteger,
        ForeignKey("bots.id", name="fk_positions_bot"),
        nullable=False,
    )
    symbol_id = Column(
        BigInteger,
        ForeignKey("symbols.id", name="fk_positions_symbol"),
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
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)"),
    )
