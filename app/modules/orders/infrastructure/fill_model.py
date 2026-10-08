# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/infrastructure/fill_model.py
#
# Modelo SQLAlchemy para la tabla `fills`.
# Un fill es la ejecución (parcial o total) de una orden.
# ======================================================================

from sqlalchemy import BigInteger, CheckConstraint, Column, ForeignKey, Index, NUMERIC, String, text
from sqlalchemy.dialects.mysql import TIMESTAMP

from app.extensions.db import Base, MYSQL_TABLE_OPTIONS


class FillModel(Base):
    """Modelo SQLAlchemy para la tabla `fills`."""

    __tablename__ = "fills"
    __table_args__ = (
        Index("idx_fills_order_ts", "order_id", "ts"),
        Index("idx_fills_exchange_trade_id", "exchange_trade_id"),
        CheckConstraint(
            "`qty` > 0 AND `price` >= 0 AND `fee` >= 0",
            name="chk_fills_qty_price",
        ),
        MYSQL_TABLE_OPTIONS,
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    order_id = Column(
        BigInteger,
        ForeignKey("orders.id", name="fk_fills_order", ondelete="CASCADE"),
        nullable=False,
    )

    # ID de la transacción en el exchange (None en modo paper)
    exchange_trade_id = Column(String(128), nullable=True)

    # Timestamp de la ejecución
    ts = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )

    # Detalles de la ejecución
    qty = Column(NUMERIC(30, 12), nullable=False)
    price = Column(NUMERIC(30, 12), nullable=False)
    fee = Column(NUMERIC(30, 12), nullable=False, server_default=text("'0.000000000000'"))
    fee_asset = Column(String(32), nullable=True)  # ej: "BNB", "USDT"

    created_at = Column(
        TIMESTAMP(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
