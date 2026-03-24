# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/infrastructure/fill_model.py
#
# Modelo SQLAlchemy para la tabla `fills`.
# Un fill es la ejecución (parcial o total) de una orden.
# ======================================================================

from sqlalchemy import BigInteger, Column, ForeignKey, NUMERIC, String, TIMESTAMP, text

from app.extensions.db import Base


class FillModel(Base):
    """Modelo SQLAlchemy para la tabla `fills`."""

    __tablename__ = "fills"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    order_id = Column(
        BigInteger,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ID de la transacción en el exchange (None en modo paper)
    exchange_trade_id = Column(String(128), nullable=True, index=True)

    # Timestamp de la ejecución
    ts = Column(
        TIMESTAMP(6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )

    # Detalles de la ejecución
    qty = Column(NUMERIC(30, 12), nullable=False)
    price = Column(NUMERIC(30, 12), nullable=False)
    fee = Column(NUMERIC(30, 12), nullable=False, server_default=text("'0.000000000000'"))
    fee_asset = Column(String(32), nullable=True)  # ej: "BNB", "USDT"

    created_at = Column(
        TIMESTAMP(6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
